from flask import Flask, render_template
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy

from .config import settings

# Flask
app = Flask(__name__)
app.config.from_object(settings)

# Database
app.config[
    "SQLALCHEMY_DATABASE_URI"
] = settings.SQLALCHEMY_DATABASE_URI.unicode_string()
db = SQLAlchemy(app)

# Bcrypt
bcrypt = Bcrypt(app)

# Login Manager
login_manager = LoginManager(app)
login_manager.refresh_view = "auth.login"
login_manager.needs_refresh_message = "Por favor vuelva a loguearse!!!"
login_manager.needs_refresh_message_category = "info"

# Mail
mail = Mail(app)

# Moment
moment = Moment(app)

# Blueprints
from app.views.home import home  # type: ignore  # noqa

app.register_blueprint(home.home_bp)

from app.views.about import about  # type: ignore  # noqa

app.register_blueprint(about.about_bp)

from app.views.auth import auth  # type: ignore  # noqa

app.register_blueprint(auth.auth_bp)

from app.views.account import account  # type: ignore  # noqa

app.register_blueprint(account.account_bp)

from app.views.posts import posts  # type: ignore  # noqa

app.register_blueprint(posts.posts_bp)

from app.views.user import user  # type: ignore  # noqa

app.register_blueprint(user.user_bp)

from app.views.admin import admin  # type: ignore  # noqa

app.register_blueprint(admin.admin_bp)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template("errors/500.html"), 500
