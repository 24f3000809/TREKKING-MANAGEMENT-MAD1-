from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(25), nullable=False)
    phone = db.Column(db.String(15))
    is_approved = db.Column(db.Boolean, default=False)
    is_blacklisted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime , default=datetime.utcnow)

    bookings = db.relationship("Booking", backref="user", lazy=True)
    staff_profile = db.relationship("StaffProfile", backref="user", uselist=False)
    assigned_treks = db.relationship("Trek", backref="staff", lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class Trek(db.Model):
    __tablename__="treks"
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    difficulty = db.Column(db.String(50), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(100),nullable=False,default="Pending")
    description = db.Column(db.Text, nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    bookings = db.relationship("Booking", backref="trek", lazy=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)



class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"))
    booking_date = db.Column(db.DateTime)
    status = db.Column(db.String(30), default="Booked")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class StaffProfile(db.Model):
    __tablename__ = "staff_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    experience = db.Column(db.Integer)
    address = db.Column(db.Text)
    emergency_contact = db.Column(db.String(20))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)







