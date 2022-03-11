import os
import time
import json

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Show portfolio of stocks"""
    user_info = db.execute("SELECT cash,username FROM users WHERE id = ?", session["user_id"])
    if request.method == "GET":
        transactions = db.execute(
            "SELECT shares, stock_symbol,stock_name,price FROM transactions WHERE user_id = ? ORDER BY id DESC",
            session["user_id"])
        symbol = db.execute("SELECT stock_symbol FROM transactions WHERE user_id = ?", session["user_id"])
        prices = {}
        for dic in symbol:
            prices[dic["stock_symbol"]] = lookup(dic["stock_symbol"])["price"]
        return render_template("index.html", transactions=transactions, user_cash=user_info[0]["cash"], prices=prices, username=user_info[0]["username"])
    if request.method == "POST":
        response = request.form.get("stocks")
        res = json.loads(response)
        print(res)
        total = 0
        # Still have no idea how to refactor this mess
        for dic in res:
            if dic["shares"] == "":
                dic["shares"] = 0
            shares = db.execute("SELECT shares FROM transactions WHERE stock_symbol = ? AND user_id = ?",
                                dic["stocks"], session["user_id"])
            s = int(dic["shares"]) - int(shares[0]["shares"])
            price = lookup(dic["stocks"])["price"]
            total += (float(price) * s)
        new_user_cash = user_info[0]["cash"] - float(total)
        if new_user_cash < 0:
            return apology("Not enough money", 400)
        for dic in res:
            shares = db.execute("SELECT shares FROM transactions WHERE stock_symbol = ? AND user_id = ?",
                                dic["stocks"], session["user_id"])
            s = int(dic["shares"]) - int(shares[0]["shares"])
            price = lookup(dic["stocks"])["price"]
            if s != 0:
                db.execute("INSERT INTO history(user_id,symbol,shares,price,time) VALUES(?,?,?,?,?)",
                           session["user_id"], dic["stocks"], s, price, time.strftime('%Y-%m-%d %H:%M:%S'))
            if int(dic["shares"]) == 0:
                db.execute("DELETE FROM transactions WHERE stock_symbol = ? AND user_id = ?",
                           dic["stocks"], session["user_id"])
            db.execute("UPDATE transactions SET shares = ? WHERE user_id = ? AND stock_symbol = ?",
                       dic["shares"], session["user_id"], dic["stocks"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_user_cash, session["user_id"])
        return redirect("/")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""
    if request.method == "GET":
        return render_template("buy.html")
    else:
        symbol = request.form.get("symbol").upper().strip()
        shares = request.form.get("shares")
        if shares == "":
            return apology("Please provied shares", 400)
        try:
            shares = int(shares)
        except ValueError:
            return apology("Invalid number of shares", 400)
        if symbol == "":
            return apology("Stock symbol can't be blank")
        stock = lookup(symbol)
        if stock == None:
            return apology("Stock not found", 400)
        if shares <= 0:
            return apology("Share has to be greater than 0", 400)
        user_shares = db.execute("SELECT shares FROM transactions WHERE user_id = ? AND stock_symbol = ?",
                                 session["user_id"], symbol)
        tmp_share = shares
        total_price = stock["price"] * tmp_share
        if user_shares:
            shares += user_shares[0]["shares"]
        user_cash = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        if float(user_cash[0]["cash"]) - total_price < 0:
            return apology("Not enough money", 400)
        db.execute("REPLACE INTO transactions(user_id,stock_symbol,stock_name,price,shares) VALUES(?,?,?,?,?)",
                   session["user_id"], symbol, stock["name"], stock["price"], shares)
        db.execute("UPDATE users SET cash = cash - ? WHERE id = ?", total_price, session["user_id"])
        db.execute("INSERT INTO history(user_id,symbol,shares,price,time) VALUES(?,?,?,?,?)",
                   session["user_id"], symbol, shares, stock["price"], time.strftime('%Y-%m-%d %H:%M:%S'))
        return redirect("/")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    history = db.execute("SELECT symbol,shares,price,time FROM history WHERE user_id = ? ORDER BY time DESC", session["user_id"])
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 400)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 400)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 400)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "GET":
        return render_template("quote.html")
    else:
        symbol = request.form.get("symbol")
        stock = lookup(symbol)
        if stock == None:
            return apology("Stock not found", 400)

        return render_template("quoted.html", stock=stock)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        usernames = db.execute("SELECT username FROM users")
        username = request.form.get("username")
        for value in usernames:
            if value["username"] == username:
                return apology("username already exist", 400)
        if username == "":
            return apology("username can't be blank", 400)
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password == "" or confirmation == "":
            return apology("password fields can't be blank", 400)
        elif password != confirmation:
            return apology("the passwords don't match", 400)
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users(username,hash) VALUES (?,?)", username, hash)
        return redirect("/")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "GET":
        symbol = db.execute("SELECT DISTINCT stock_symbol FROM transactions WHERE user_id = ?", session["user_id"])
        return render_template("sell.html", symbol=symbol)
    else:
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if shares == "":
            return apology("Please provide shares")
        shares = int(shares)
        if symbol == None:
            return apology("Stock symbol can't be blank", 400)
        stock = lookup(symbol)
        user_shares = db.execute("SELECT shares FROM transactions WHERE user_id = ? AND stock_symbol = ?",
                                 session["user_id"], symbol)
        if stock == None:
            return apology("Stock not found", 400)
        if shares <= 0 or shares == "":
            return apology("Share has to be greater than 0", 400)
        if shares > user_shares[0]["shares"]:
            return apology("Too much shares")
        price = db.execute("SELECT price FROM transactions WHERE stock_symbol = ? AND user_id = ?", symbol, session["user_id"])
        db.execute("UPDATE users SET cash = cash + ? WHERE id = ?", (price[0]["price"] * shares), session["user_id"])
        if shares == user_shares[0]["shares"]:
            db.execute("DELETE FROM transactions WHERE user_id = ? AND stock_symbol = ?", session["user_id"], symbol)
        else:
            db.execute("UPDATE transactions SET shares = shares - ? WHERE user_id = ? AND stock_symbol = ?",
                       shares, session["user_id"], symbol)
        db.execute("INSERT INTO history(user_id,symbol,shares,price,time) VALUES(?,?,?,?,?)",
                   session["user_id"], symbol, -shares, price[0]["price"], time.strftime('%Y-%m-%d %H:%M:%S'))
        return redirect("/")


@app.route("/password", methods=["GET", "POST"])
@login_required
def password():
    if request.method == "GET":
        return render_template("password.html")
    if request.method == "POST":
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        old = request.form.get("old_pass")
        hash = db.execute("SELECT hash FROM users WHERE id = ?", session["user_id"])
        if not check_password_hash(hash[0]["hash"], old):
            return apology("invalid password", 400)
        if password == "" or confirmation == "":
            return apology("password fields can't be blank", 400)
        elif password != confirmation:
            return apology("the passwords don't match", 400)
        hash = generate_password_hash(password)
        db.execute("UPDATE users SET hash = ? WHERE id = ?", hash, session["user_id"])
        return redirect("/")


@app.route("/money", methods=["GET", "POST"])
@login_required
def money():
    if request.method == "GET":
        return render_template("money.html")
    else:
        cash = request.form.get("cash")
        if cash == None or cash == 0:
            return apology("Please provide the money", 400)
        db.execute("UPDATE users SET cash = cash + ?", cash)
        return redirect("/")