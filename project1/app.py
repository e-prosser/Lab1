import os
import requests

from flask import Flask, session, render_template, request, redirect, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

# Rout to main page or log in page
@app.route("/")
def index():
    # If user is signed in, go to homepage
    if session.get("username") is not None:
        return render_template("home.html", username = session.get("username"))
    # Otherwise direct to login page
    return render_template("login.html")


# Main page, assess user credentials
@app.route("/home", methods=["POST"])
def home():
	session.clear()

    # Get current log in username
	username = request.form.get("username")

    # get user password from db
	db_password = db.execute("SELECT password FROM USERS WHERE username = :username", {"username": username}).fetchone()

    # If password exists (ie. the user is registered)
	if db_password != None:
        # User inputted password
		password = request.form.get("password")
        # Check to make sure passwords match
		if password == db_password[0]:
            # Establish session for user
			session["username"] = username
            # Render homepage template
			return render_template("home.html", username = username)

    # Else direct to sign up
	else:
		return redirect("/register")
	return render_template("login.html")


@app.route("/login", methods=["POST"])
def login():
    # Start new session for user
	session.clear()
    # User input
	username = request.form.get("username")
	password = request.form.get("password")
    # Insert
	db.execute("INSERT INTO users (username, password) VALUES (:username, :password)",{"username": username, "password": password})
	db.commit()
	session["username"] = username
	return render_template("home.html", username = username)


@app.route("/register")
def register():
	if session.get("username") is not None:
		return render_template("home.html", username = session.get("username"))
	return render_template("register.html")



@app.route("/results", methods=["POST"])
def results():
    # Pull requests from form
    isbn = request.form.get("isbn")
    name = request.form.get("name")
    author = request.form.get("author")

    # Check which part of the form is filled, run approriate query
    if len(isbn) < 1:
        ans = one_arg("name", name) if len(author)==0 else one_arg("author", author) if len(name)==0 else two_args("name", name, "author", author)
    elif len(name) < 1:
        ans = one_arg("isbn", isbn) if len(author)==0 else one_arg("author", author) if len(isbn)==0 else two_args("isbn", isbn, "author", author)
    elif len(author) < 1:
        ans = one_arg("isbn", isbn) if len(name)==0 else one_arg("name", name) if len(isbn)==0 else two_args("isbn", isbn, "name", name)
    else:
        # Select row on all columns
        ans = db.execute(f"SELECT * FROM books WHERE isbn LIKE '%{isbn}%' AND name LIKE '%{name}%' AND author LIKE '%{author}%'").fetchall()
    return render_template("results.html", ans = ans)

# To compare one user input to database
def one_arg(user_param, db_value):
	ans = db.execute(f"SELECT * FROM books WHERE {user_param} LIKE '%{db_value}%'").fetchall()
	return ans

# To compare 2 user inputs to database
def two_args(u1, bd1, u2, db2):
	ans = db.execute(f"SELECT * FROM books WHERE {u1} LIKE '%{bd1}%' AND {u2} LIKE '%{db2}%'").fetchall()
	return ans


@app.route("/details/<isbn>", methods=["GET","POST"])
def details(isbn):
    book = {}
    reviews = []
    # Retreive infromation
    book["isbn"] = request.values.get("isbn")
    book["title"] = request.values.get("title")
    book["author"] = request.values.get("author")
    book["year"] = request.values.get("year")
    print(book)

    # Set up API
    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": f"isbn:{book['isbn']}"})
    j_res = res.json()

    res = requests.get("https://www.googleapis.com/books/v1/volumes", params={"q": "isbn:080213825X"})
    print(res.json())

    #get  previous reviews
    reviews = db.execute("SELECT rating, review FROM reviews WHERE book = :isbn", {"isbn": isbn}).fetchall()
    # Render template for book details
    return render_template("/details.html", res = book, reviews = reviews)


@app.route("/review", methods=["GET", "POST"])
def review():
    isbn = request.values.get("isbn")
    rating = request.values.get("rating")
    review = request.values.get("review")
    rating = 5
    isbn = "068987121X"
    review = 'Great!'
    db.execute("INSERT INTO reviews (book, rating, review) VALUES (:isbn, :rating, :review)", {"isbn":isbn, "rating":rating, "review":review})
    db.commit()

    # Returns to begining search
    return redirect("/")


# Logout, clear session, return to start
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
