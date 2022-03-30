from flask import Blueprint, redirect, render_template, url_for, flash, request
from .forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from .models import User
from app import db, bcrypt, mail, login_manager
from flask_login import login_required, login_user, logout_user, current_user
import pprint
from flask_mail import Message

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')

@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('home.home_view')
            return redirect(next)
        flash(f"Error al loguearse", category="danger")
    return render_template('login.html', form=form)


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
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.home_view"))

def send_email(user):
    token = user.get_token()
    msg = Message(
        subject="Password Reset Request", 
        recipients=[user.email],
        sender="noreplay@test.com"
    )
    msg.body = f""" Ingrese al siguiente link para resetear la password:

    { url_for("auth.reset_token", token=token, _external=True) }
    
    """
    mail.send(msg)
    pprint.PrettyPrinter().pprint(url_for("auth.reset_token", token=token, _external=True))


@auth_bp.route("/reset_password/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email(user)
            flash("Solicitud de reseteo de password enviada, revise su", category="success")
            return redirect(url_for("auth.login"))
        else:
            flash("Email no registrado, por favor registrese", category="danger")
            return redirect(url_for("auth.register"))
    return render_template("reset_password.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    user = User.verify_token(token)
    if user is None:
        flash("Token invalido", category="warning")
        return redirect(url_for("auth.reset_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.password = encrypted_password
        db.session.commit()
        flash("Password cambiado", category="success")
        return redirect(url_for("auth.login"))
    
    return render_template("change_password.html", form=form)