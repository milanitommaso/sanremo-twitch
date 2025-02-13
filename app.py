from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import json
from datetime import timedelta

from chat_listener import start_threads, stop_threads

app = Flask(__name__)
app.config["DEBUG"] = True
app.secret_key = "hello"
app.pemanent_session_lifetime = timedelta(days=7)


@app.route("/")
def index():
    if "user" not in session:
        return "Unauthorized", 401
    
    return render_template("index.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":

        with open("secrets.json", 'r') as f:
            password = json.load(f)["password"]

        username = request.form["username"]
        password_in = request.form["password"]
        if username == "admin" and password_in == password:

            session.permanent = True
            session['user'] = username

            return redirect(url_for("index"))
        else:
            return render_template("login.html")
        
    if request.method == "GET":
        return render_template("login.html")


@app.route("/api/get-singers/<day>")
def get_singers(day):
    if "user" not in session:
        return "Unauthorized", 401

    try:
        with open("singers_songs.json", 'r') as f:
            singers_songs = json.load(f)[day]
    except:
        singers_songs = {}

    return jsonify(singers_songs)


@app.route("/api/get-votes/<day>")
def get_averages(day):
    if "user" not in session:
        return "Unauthorized", 401
    
    try:
        with open("grades.json", 'r') as f:
            grades = json.load(f)[day]
    except:
        grades = {}

    return jsonify(grades)


@app.route("/api/start-listen/<day>/<singer_id>")
def start_listen(day, singer_id):
    if "user" not in session:
        return "Unauthorized", 401
    
    start_threads(day, singer_id)
    return {"started": True}


@app.route("/api/stop-listen")
def stop_listen():
    if "user" not in session:
        return "Unauthorized", 401
    
    stop_threads()
    return {"stopped": True}


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8000)
