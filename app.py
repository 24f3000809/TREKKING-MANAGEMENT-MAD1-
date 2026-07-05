from flask import Flask, render_template, request, redirect, session 
from config import Config
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)

with app.app_context():
    db.create_all()

    admin = User.query.filter_by(email="admin@trek.com").first()

    if not admin:
        admin = User(
            name="Admin",
            email="admin@trek.com",
            password=generate_password_hash("admin123"),
            role="admin",
            phone="9999999999",
            is_approved=True
        )

        db.session.add(admin)
        db.session.commit()


@app.route("/")
def home():
    return "<h1>Trekking Management Application</h1>"

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]

        if password != confirm_password:
            return "Passwords do not match"

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            return "Email already exists"

        if role == "staff":
            approval = False
        else:
            approval = True

        new_user = User(
            name=name,
            email=email,
            password=generate_password_hash(password),
            role=role,
            phone=phone,
            is_approved=approval
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect("/")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if not user:
            return "User does not exist"

        if not check_password_hash(user.password, password):
            return "Incorrect Password"

        if user.is_blacklisted:
            return "You are blacklisted"

        if user.role == "staff" and not user.is_approved:
            return "Waiting for Admin Approval"

        session["user_id"] = user.id
        session["user_name"] = user.name
        session["role"] = user.role

        if user.role == "admin":
            return redirect("/admin")

        elif user.role == "staff":
            return redirect("/staff")

        else:
            return redirect("/user")

    return render_template("login.html")

@app.route("/admin")
def admin_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    return "<h1>Admin Dashboard</h1>"


@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    return "<h1>Staff Dashboard</h1>"


@app.route("/user")
def user_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"
        
    return "<h1>User Dashboard</h1>"

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)