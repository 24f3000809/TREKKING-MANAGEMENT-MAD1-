from flask import Flask
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

@app.route("/")
def home():
    return "<h1>Trekking Management Application</h1>"

if __name__ == "__main__":
    app.run(debug=True)