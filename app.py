from flask import Flask, render_template, request, redirect, session 
from config import Config
from models import db, User, Trek, Booking, StaffProfile
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import or_

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

    total_treks = Trek.query.count()
    total_users = User.query.filter_by(role="user").count()
    total_staff = User.query.filter_by(role="staff").count()
    total_bookings = Booking.query.count()

    return render_template("admin_dashboard.html",
    total_treks=total_treks,
    total_users=total_users,
    total_staff=total_staff,
    total_bookings=total_bookings)

@app.route("/staff")
def staff_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    staff_id = session["user_id"]

    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=staff_id
    ).all()

    participant_count = {}

    for trek in assigned_treks:
        participant_count[trek.id] = Booking.query.filter_by(
            trek_id=trek.id
        ).count()

    return render_template(
        "staff_dashboard.html",
        assigned_treks=assigned_treks,
        participant_count=participant_count
    )

@app.route("/update-trek/<int:trek_id>", methods=["GET", "POST"])
def update_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        return "Access Denied"

    if request.method == "POST":

        trek.available_slots = int(request.form["available_slots"])
        trek.status = request.form["status"]

        db.session.commit()

        return redirect("/staff")

    return render_template(
        "update_trek.html",
        trek=trek
    )

@app.route("/participants/<int:trek_id>")
def participants(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "staff":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if trek.assigned_staff_id != session["user_id"]:
        return "Access Denied"

    bookings = Booking.query.filter_by(
        trek_id=trek.id
    ).all()

    return render_template(
        "participants.html",
        trek=trek,
        bookings=bookings
    )


@app.route("/manage-staff")
def manage_staff():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff_members = User.query.filter_by(role="staff").all()

    treks = Trek.query.all()

    return render_template(
        "manage_staff.html",
        staff_members=staff_members,
        treks=treks
    )

@app.route("/approve-staff/<int:staff_id>", methods=["POST"])
def approve_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = User.query.get_or_404(staff_id)

    staff.is_approved = True

    db.session.commit()

    return redirect("/manage-staff")

@app.route("/blacklist-staff/<int:staff_id>", methods=["POST"])
def blacklist_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = User.query.get_or_404(staff_id)

    staff.is_blacklisted = True

    db.session.commit()

    return redirect("/manage-staff")

@app.route("/unblacklist-staff/<int:staff_id>", methods=["POST"])
def unblacklist_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    staff = User.query.get_or_404(staff_id)

    staff.is_blacklisted = False

    db.session.commit()

    return redirect("/manage-staff")

@app.route("/assign-staff/<int:staff_id>", methods=["POST"])
def assign_staff(staff_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(request.form["trek_id"])

    trek.assigned_staff_id = staff_id

    db.session.commit()

    return redirect("/manage-staff")


@app.route("/treks", methods=["GET", "POST"])
def manage_treks():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    if request.method == "POST":

        trek = Trek(
            trek_name=request.form["trek_name"],
            location=request.form["location"],
            difficulty=request.form["difficulty"],
            duration=int(request.form["duration"]),
            available_slots=int(request.form["available_slots"]),
            start_date=datetime.strptime(
                request.form["start_date"],
                "%Y-%m-%dT%H:%M"
            ),
            end_date=datetime.strptime(
                request.form["end_date"],
                "%Y-%m-%dT%H:%M"
            ),
            description=request.form["description"]
        )

        db.session.add(trek)
        db.session.commit()

        return redirect("/treks")

    treks = Trek.query.all()

    return render_template(
        "manage_treks.html",
        treks=treks
    )

@app.route("/edit-trek/<int:trek_id>", methods=["GET", "POST"])
def edit_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    if request.method == "POST":

        trek.trek_name = request.form["trek_name"]
        trek.location = request.form["location"]
        trek.difficulty = request.form["difficulty"]
        trek.duration = int(request.form["duration"])
        trek.available_slots = int(request.form["available_slots"])
        trek.status = request.form["status"]
        trek.description = request.form["description"]

        db.session.commit()

        return redirect("/treks")

    return render_template(
        "edit_trek.html",
        trek=trek
    )

@app.route("/delete-trek/<int:trek_id>", methods=["POST"])
def delete_trek(trek_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    trek = Trek.query.get_or_404(trek_id)

    db.session.delete(trek)

    db.session.commit()

    return redirect("/treks")


@app.route("/user")
def user_dashboard():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "user":
        return "Access Denied"

    return "<h1>User Dashboard</h1>"

@app.route("/manage-users")
def manage_users():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    users = User.query.filter_by(role="user").all()

    return render_template(
        "manage_users.html",
        users=users
    )

@app.route("/blacklist-user/<int:user_id>", methods=["POST"])
def blacklist_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = True

    db.session.commit()

    return redirect("/manage-users")

@app.route("/unblacklist-user/<int:user_id>", methods=["POST"])
def unblacklist_user(user_id):

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    user = User.query.get_or_404(user_id)

    user.is_blacklisted = False

    db.session.commit()

    return redirect("/manage-users")

@app.route("/search", methods=["GET","POST"])
def search():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    users = []
    staff_members = []
    treks = []

    if request.method == "POST":

        keyword = request.form["keyword"]

        users = User.query.filter(
            User.role=="user",
            or_(
                User.name.ilike(f"%{keyword}%"),
                User.id==keyword
            )
        ).all()

        staff_members = User.query.filter(
            User.role=="staff",
            or_(
                User.name.ilike(f"%{keyword}%"),
                User.id==keyword
            )
        ).all()

        treks = Trek.query.filter(
            or_(
                Trek.trek_name.ilike(f"%{keyword}%"),
                Trek.id==keyword
            )
        ).all()

    return render_template(
        "search.html",
        users=users,
        staff_members=staff_members,
        treks=treks
    )

@app.route("/bookings")
def view_bookings():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    bookings = Booking.query.all()

    return render_template(
        "view_bookings.html",
        bookings=bookings
    )

@app.route("/history")
def trek_history():

    if "user_id" not in session:
        return redirect("/login")

    if session["role"] != "admin":
        return "Access Denied"

    bookings = Booking.query.all()

    return render_template(
        "trek_history.html",
        bookings=bookings
    )

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)