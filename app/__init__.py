from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://flaskuser:flaskpassword@localhost:5432/flaskdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
db.create_all()

from .home import home
app.register_blueprint(home.home_bp)

from .about import about
app.register_blueprint(about.about_bp)

from .auth import auth
app.register_blueprint(auth.auth_bp)