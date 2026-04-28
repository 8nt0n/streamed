import os

import subprocess
import sys
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, make_response, url_for
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
import datetime

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024 * 1024 # kaplau... kaboom max upload file size is now 200GB
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///streamed.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# --------------------------index--------------------------#

@app.route("/")
@login_required
def index():

    if request.method == "POST":
        return apology("TODO")
    else:
        return render_template("index.html")


# --------------------------login--------------------------#

@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        if not request.form.get("username"):
            return apology("must provide username", 403)

        elif not request.form.get("password"):
            return apology("must provide password", 403)

        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]

        return redirect("/")
    else:
        return render_template("login.html")


# --------------------------logout--------------------------#

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


# --------------------------register--------------------------#

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":

        # just some shit that could go wrong (if the user has like... potatoe iq)
        if not request.form.get("username"):
            return apology("must provide username", 400)

        if not request.form.get("password"):
            return apology("must provide password", 400)

        if not request.form.get("confirmation"):
            return apology("must provide password confirmation", 400)

        if request.form.get("confirmation") != request.form.get("password"):
            return apology("passwords dont match", 400)

        # Insert into db
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?);", request.form.get(
                "username"), generate_password_hash(request.form.get("password")))
        except ValueError:
            return apology("User already exists", 400)

        return redirect("/")

    else:
        return render_template("register.html")


# --------------------------upload--------------------------#

@app.route("/upload_movie", methods=["GET", "POST"]) 
def upload():
    if request.method == "GET":
        return render_template("upload_movie.html")
    
    if request.method == "POST":

        
        movie_name = secure_filename(request.form.get("moviename")) # this makes sure bad people cant come into the code :)
        description = request.form.get("description")
        movie_file = request.files.get("movie_file")
        poster_file = request.files.get("poster_file")


        # like check if eversthing has been typed in
        if not movie_name:
            return apology("missing movie name", 400)

        if not description:
            return apology("missing description", 400)

        if not movie_file:
            return apology("missing movie file", 400)

        if not poster_file:
            return apology("missing poster image", 400)
        
        # check for right fileformat 
        if not movie_file.filename.endswith(".mp4"):
            return apology("movie must be mp4", 400)
        
        if not poster_file.filename.endswith(".png"):
            return apology("poster must be png", 400)


        # try to create a folder or if the user is stupid dont (no its fine we all forget how our movies are named)
        try:
            os.makedirs(f"static/media/movies/{movie_name}/meta", exist_ok=False) 
        except FileExistsError:
            return apology("movie already exists")
        
        # write the description for the movie into description.txt
        with open(f"static/media/movies/{movie_name}/meta/description.txt", "w") as descriptionFile:
            descriptionFile.write(description)

        # save the video and img
        movie_file.save(f"static/media/movies/{movie_name}/{movie_name}.mp4")
        poster_file.save(f"static/media/movies/{movie_name}/meta/thumbnail.png")

        # run refresh.py (man tbh i dont know if thats the clean way to do this, desperate times ok?)
        script_path = "static/_tools/refresh.py"
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True
        )

        print(result)        

        return redirect("/")