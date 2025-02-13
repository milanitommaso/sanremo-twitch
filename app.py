from flask import Flask, render_template, jsonify
import json

from chat_listener import start_threads, stop_threads

app = Flask(__name__)
app.config["DEBUG"] = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/get-singers/<day>")
def get_singers(day):
    try:
        with open("singers_songs.json", 'r') as f:
            singers_songs = json.load(f)[day]
    except:
        singers_songs = {}

    return jsonify(singers_songs)


@app.route("/api/get-votes/<day>")
def get_averages(day):
    try:
        with open("grades.json", 'r') as f:
            grades = json.load(f)[day]
    except:
        grades = {}

    return jsonify(grades)


@app.route("/api/start-listen/<day>/<singer_id>")
def start_listen(day, singer_id):
    start_threads(day, singer_id)
    return {"started": True}


@app.route("/api/stop-listen")
def stop_listen():
    stop_threads()
    return {"stopped": True}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
