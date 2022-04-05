from pprint import pprint
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from .config import settings

# Flask
app = Flask(__name__)
app.config.from_object(settings)

# Database
db = SQLAlchemy(app)
db.create_all()

# Bcrypt
bcrypt = Bcrypt(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.refresh_view = "auth.login"
login_manager.needs_refresh_message = (
    "Por favor vuelva a loguearse!!!"
)
login_manager.needs_refresh_message_category = "info"

# Mail
mail = Mail(app)

# Blueprints
from .home import home
app.register_blueprint(home.home_bp)

from .about import about
app.register_blueprint(about.about_bp)

from .auth import auth
app.register_blueprint(auth.auth_bp)

from .account import account
app.register_blueprint(account.account_bp)



@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500