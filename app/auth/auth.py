from flask import Blueprint, redirect, render_template, url_for, flash
from .forms import RegistrationForm, LoginForm
from .models import User
from app import db, bcrypt

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            flash(f"Login OK", category="success")
            return redirect(url_for("home.home_view"))
        else:
            flash(f"Error al loguearse", category="danger")
    return render_template("login.html", form=form)


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user = User(username=form.username.data,email=form.email.data,password=encrypted_password)
        db.session.add(user)
        db.session.commit()
        flash(f"Cuenta creada exitosamente", category="success")
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)