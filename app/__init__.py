from flask import Flask

app = Flask(__name__)


from .home import view
app.register_blueprint(view.home_bp)