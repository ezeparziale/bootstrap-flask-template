from flask import Blueprint, redirect, render_template, url_for, flash
from .forms import RegistrationForm, LoginForm, ResetPasswordForm
from .models import User
from app import db, bcrypt
from flask_login import login_user, logout_user, current_user

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash(f"Login OK", category="success")
            return redirect(url_for("home.home_view"))
        else:
            flash(f"Error al loguearse", category="danger")
    return render_template("login.html", form=form)


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))
    form = RegistrationForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data,email=form.email.data,password=encrypted_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Cuenta creada exitosamente", category="success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/logout/")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))


@auth_bp.route("/reset_password/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash("Solicitud de reseteo de password enviada, revise su", category="success")
            return redirect(url_for("auth.login"))
        else:
            flash("Email no registrado, por favor registrese", category="danger")
            return redirect(url_for("auth.register"))
    return render_template("reset_password.html", form=form)