from flask import Flask

app = Flask(__name__)


from .home import home
app.register_blueprint(home.home_bp)

from .about import about
app.register_blueprint(about.about_bp)