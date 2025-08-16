from flask import Flask, render_template, request, redirect
import sqlite3
import flask_login

app = Flask(__name__)
app.secret_key = "your_secret_key"
login_manager = flask_login.LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" #type: ignore

class User(flask_login.UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Simple in-memory user storage (in production, use a database)
users = {"admin": {"password": "password", "id": "admin"}}

@login_manager.user_loader
def load_user(user_id):
    for username, user_data in users.items():
        if user_data["id"] == user_id:
            return User(user_id, username)
    return None

# Ensure the table exists
def init_db():
    with sqlite3.connect("stats.db") as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                points INTEGER NOT NULL
            )
        """)

init_db()



@app.route("/", methods=["GET", "POST"])
@flask_login.login_required
def index():
    print("Current user authenticated:", flask_login.current_user.is_authenticated)
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        points = request.form["points"]
        with sqlite3.connect("stats.db") as cx:
            cx.execute(
                "INSERT INTO stats (name, date, points) VALUES (?, ?, ?)",
                (name, date, points)
            )
    with sqlite3.connect("stats.db") as cx:
        cx.row_factory = sqlite3.Row
        stats = cx.execute("SELECT * FROM stats").fetchall()
    return render_template("index.html", stats=stats)


@app.route("/delete/<int:stat_id>")
@flask_login.login_required
def delete(stat_id):
    with sqlite3.connect("stats.db") as cx:
        cx.execute("DELETE FROM stats WHERE id = ?", (stat_id,))
    return redirect("/")

@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        if username in users and users[username]["password"] == password:
            user = User(id=users[username]["id"], username=username)
            flask_login.login_user(user)
            return redirect("/")
        else:
            return render_template("login.html", error="Invalid credentials")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        
        # Validation
        if username in users:
            return render_template("register.html", error="Username already exists")
        
        if password != confirm_password:
            return render_template("register.html", error="Passwords don't match")
        
        if len(password) < 4:
            return render_template("register.html", error="Password must be at least 4 characters")
        
        # Create new user
        user_id = f"user_{len(users)}"
        users[username] = {"password": password, "id": user_id}
        
        # Log them in automatically
        user = User(id=user_id, username=username)
        flask_login.login_user(user)
        return redirect("/")
    
    return render_template("register.html")

@app.route("/logout")
@flask_login.login_required
def logout():
    flask_login.logout_user()
    return redirect("/login")

@app.route("/favicon.ico")
def favicon():
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
# This code is a simple Flask application that allows users to register, log in, and manage statistics.
