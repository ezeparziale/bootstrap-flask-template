from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET_KEY"
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://flaskuser:flaskpassword@localhost:5432/flaskdb"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
db.create_all()

bcrypt = Bcrypt(app)

login_manager = LoginManager(app)
login_manager.refresh_view = "auth.login"
login_manager.needs_refresh_message = (
    "Por favor vuelva a loguearse!!!"
)
login_manager.needs_refresh_message_category = "info"

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "MY_EMAIL"
app.config["MAIL_PASSWORD"] = "MY_PASSWORD"

mail = Mail(app)

from .home import home
app.register_blueprint(home.home_bp)

from .about import about
app.register_blueprint(about.about_bp)

from .auth import auth
app.register_blueprint(auth.auth_bp)

from .account import account
app.register_blueprint(account.account_bp)