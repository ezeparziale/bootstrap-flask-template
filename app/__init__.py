from flask import Flask

app = Flask(__name__)
app.config["SECRET_KEY"] = "SECRET_KEY"

from .home import home
app.register_blueprint(home.home_bp)

from .about import about
app.register_blueprint(about.about_bp)

from .auth import auth
app.register_blueprint(auth.auth_bp)