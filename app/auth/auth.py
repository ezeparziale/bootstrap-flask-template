from flask import Blueprint, redirect, render_template, url_for
from .forms import RegistrationForm, LoginForm

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        return redirect(url_for("home.home_view"))
    return render_template("login.html", form=form)


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)