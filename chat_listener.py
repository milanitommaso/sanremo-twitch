import time
import threading
import socket
import random
import json

threads = []
channels = []

lock = threading.Lock()

def process_message(line: str, day, singer_id):
    username, message = None, None

    print(line)

    line_list = line.split(";")
    for e in line_list:
        if "display-name=" in e and "reply" not in e:
            username = e.split("=")[1]
            # make username lowercase
            username = username.lower()

    if username is None:
        return

    # get the message
    try:
        message = "".join(line.split("PRIVMSG #")[1].split(" :")[1]).strip()

        if "NaN" in message or "inf" in message or "INF" in message or "nan" in message or "Nan" in message:
            return

        # check if the message represent a grade
        # possible grades: only a number from 0 to 10 or <grade>/10

        if '/10' in message:
            message = message.split('/10')[0]

        message = message.replace(",", ".")

        # convert the message to a float
        grade = float(message)

        if grade < 0 or grade > 10:
            return

        # the lock garantee that the file is not modified by multiple threads at the same time
        with lock:
            # open the file where the grades are stored and check if the user has already voted
            with open("grades.json", 'r') as f:
                grades = json.load(f)

            if singer_id not in grades[day]:
                grades[day][singer_id] = {}

            if username in channels:
                if "streamers" not in grades[day][singer_id]:
                    grades[day][singer_id]["streamers"] = {}

                grades[day][singer_id]["streamers"][username] = grade

            else:
                if username in grades[day][singer_id]:
                    # user has already voted
                    return
                
                # save the new grade
                grades[day][singer_id][username] = grade

            with open("grades.json", 'w') as f:
                json.dump(grades, f, indent=4)

    except:
        message = None
    
    return


class ListenChatThread(threading.Thread):
    def __init__(self, channel, day, singer_id):
        global SERVER, PASSWORD, NICK

        super(ListenChatThread, self).__init__()
        self._stop_event = threading.Event()
        self.channel = channel
        self.singer_id = singer_id
        self.day = day
        self.socket_irc = None
        self._reloading_irc_connection = threading.Event()

        with open("secrets.json", "r") as f:
            secrets = json.load(f)
            SERVER = secrets["SERVER"]
            PASSWORD = secrets["PASSWORD"]
            NICK = secrets["NICK"]

    def set_stop(self):
        self._stop_event.set()

    def is_stopped(self):
        return self._stop_event.is_set()

    def set_reloading_irc_connection(self):
        self._reloading_irc_connection.set()

    def clear_reloading_irc_connection(self):
        self._reloading_irc_connection.clear()

    def is_reloading_irc_connection(self):
        return self._reloading_irc_connection.is_set()

    def reload_irc_connection(self):
        print(f"> Reloading irc connection for {self.channel}")
        self.set_reloading_irc_connection()     # set the flag to avoid the thread to listen the chat while reloading the connection

        time.sleep(5.5)   # wait that the thread pause the listening of the chat

        self.socket_irc.close()

        self.socket_irc = self.connect()    # set the new irc socket

        readbuffer = self.socket_irc.recv(32768).decode()
        count = 0
        while "Login unsuccessful" in readbuffer and count <= 5:
            self.socket_irc.close()
            time.sleep(random.uniform(1, 5))    # randomize the sleep
            self.socket_irc = self.connect()
            readbuffer = self.socket_irc.recv(32768).decode()
            count += 1

        if count > 5 and "Login unsuccessful" in readbuffer:
            self.socket_irc.close()
            print(f"> Login unsuccessful during reload irc connection {self.channel}")
            return -1
        
        self.socket_irc.settimeout(5)

        self.clear_reloading_irc_connection()   # clear the flag to allow the thread to listen the chat
        print(f"> Reloaded irc connection for {self.channel}")

    def connect(self):
        # print(f"\t\t CONNECTING TO {self.channel}")
        irc = socket.socket()
        irc.connect((SERVER, 6667)) #connects to the server

        #sends variables for connection to twitch chat
        irc.send(('PASS ' + PASSWORD + '\r\n').encode())
        # irc.send(('USER ' + NICK + ' 0 * :' + BOT_OWNER + '\r\n').encode())
        irc.send(('NICK ' + NICK + '\r\n').encode())

        irc.send(('CAP REQ :twitch.tv/tags\r\n').encode())
        irc.send(('CAP REQ :twitch.tv/commands\r\n').encode())
        irc.send(('raw CAP REQ :twitch.tv/membership\r\n').encode())

        irc.send(('JOIN #' + self.channel + '\r\n').encode())

        return irc
    
    def start_listen(self):
        readbuffer = ""
        count_timeout = 0
        while not self.is_stopped():
            if self.is_reloading_irc_connection():  # wait for the connection to be ready, used for the reload of the irc connection
                time.sleep(0.3)
                continue

            try:
                readbuffer = self.socket_irc.recv(32768).decode()
                count_timeout = 0
            except socket.timeout:
                count_timeout += 1
            except UnicodeDecodeError:
                pass

            if count_timeout >= 60 and not self.is_reloading_irc_connection():
                print("reloading irc connection")
                self.reload_irc_connection()
                count_timeout = 0
                continue

            lines = readbuffer.split("\n")
            for line in lines:
                if "PRIVMSG" in line:
                    process_message(line, self.day, self.singer_id)

                elif "PING" in line:
                    self.socket_irc.send(("PONG :tmi.twitch.tv\r\n").encode())

            readbuffer = ""
        
        if self.is_stopped():
            self.socket_irc.close()
            return
    
    def run(self):
        self.socket_irc = self.connect()
        readbuffer = self.socket_irc.recv(32768).decode()
        count = 0
        while "Login unsuccessful" in readbuffer and count <= 10:
            self.socket_irc.close()
            time.sleep(3)
            self.socket_irc = self.connect()
            readbuffer = self.socket_irc.recv(32768).decode()
            count += 1

        if count > 10 and "Login unsuccessful" in readbuffer:
            print(f"> Login unsuccessful {self.channel}")
            self.socket_irc.close()
            return

        self.socket_irc.settimeout(5)
        
        self.start_listen()


def start_threads(day, singer_id):
    # called after api request

    global threads, channels

    stop_threads()

    with open("secrets.json", "r") as f:
        secrets = json.load(f)
        channels = secrets["channels"]

    threads.clear()

    for c in channels:
        t = ListenChatThread(c, day, singer_id)
        threads.append(t)
        t.start()
        time.sleep(0.7)


def stop_threads():
    # called after api request

    global threads

    for t in threads:
        t.set_stop()
        t.join()

    threads.clear()

    print("threads stopped")
