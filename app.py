from flask import Flask
from config import Config
from models import db, User

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
            password="admin123",
            role="admin",
            phone="9999999999",
            is_approved=True
        )

        db.session.add(admin)
        db.session.commit()


@app.route("/")
def home():
    return "<h1>Trekking Management Application</h1>"


if __name__ == "__main__":
    app.run(debug=True)