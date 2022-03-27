from flask import Blueprint, redirect, render_template, url_for, flash
from .forms import RegistrationForm, LoginForm
from .models import User
from app import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and form.email.data==user.email and form.password.data==user.password:
            flash(f"Login OK", category="success")
            return redirect(url_for("home.home_view"))
        else:
            flash(f"Error al loguearse", category="danger")
    return render_template("login.html", form=form)


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data,email=form.email.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash(f"Cuenta creada exitosamente", category="success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)