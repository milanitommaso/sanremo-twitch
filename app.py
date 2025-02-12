from flask import Flask, render_template

from chat_listener import start_threads, stop_threads

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/get-averages/<day>")
def get_averages(day):
    return "data"


@app.route("/api/start-listen/<day>/<singer_id>")
def start_listen(day, singer_id):
    start_threads(day, singer_id)
    return "started"


@app.route("/api/stop-listen")
def stop_listen():
    stop_threads()
    return "stopped"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
