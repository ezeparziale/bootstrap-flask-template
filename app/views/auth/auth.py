from threading import Thread

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from flask_mail import Message

from app import app, bcrypt, db, mail, settings

from ...models import User
from .forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
)

auth_bp = Blueprint(
    "auth",
    __name__,
    url_prefix="/auth",
    template_folder="templates",
    static_folder="static",
)


@auth_bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if (
            not current_user.confirmed
            and request.endpoint
            and request.blueprint != "auth"
            and request.endpoint != "static"
        ):
            return redirect(url_for("auth.unconfirmed"))


@auth_bp.route("/unconfirmed/")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("home.home_view"))
    return render_template("unconfirmed.html")


@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get("next")
            if next is None or not next.startswith("/"):
                next = url_for("home.home_view")
            return redirect(next)
        flash(f"Error al loguearse", category="danger")
    return render_template("login.html", form=form)


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email_confirm(user):
    token = user.get_confirm_token()
    msg = Message(
        subject="Confirmar cuenta",
        recipients=[user.email],
        sender="noreplay@test.com",
    )
    msg.html = render_template(
        "emails/confirm_account.html", token=token, app_name=settings.SITE_NAME
    )
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


@auth_bp.route("/register/", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))
    form = RegistrationForm()
    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=encrypted_password,
            image_file=User.generate_avatar(),
        )
        db.session.add(user)
        db.session.commit()
        flash(f"Cuenta creada exitosamente", category="success")
        flash(f"Verifique su mail para confirmar cuenta", category="info")
        send_email_confirm(user)
        return redirect(url_for("auth.login"))
    return render_template("register.html", form=form)


@auth_bp.route("/logout/")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.home_view"))


def send_email_reset_password(user):
    token = user.get_token()
    msg = Message(
        subject="Password Reset Request",
        recipients=[user.email],
        sender="noreplay@test.com",
    )
    msg.html = render_template(
        "emails/reset_password.html", token=token, app_name=settings.SITE_NAME
    )
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()


@auth_bp.route("/reset_password/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email_reset_password(user)
            flash(
                "Solicitud de reseteo de password enviada, revise su email",
                category="success",
            )
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
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user.password = encrypted_password
        db.session.commit()
        flash("Password cambiado", category="success")
        return redirect(url_for("auth.login"))

    return render_template("change_password.html", form=form)


@auth_bp.route("/confirm/<token>", methods=["GET", "POST"])
@login_required
def confirm(token):
    if current_user.confirmed:
        flash("La cuenta ya se encuentra confirmada", category="info")
        return redirect(url_for("home.home_view"))
    if current_user.confirm(token):
        flash("Cuenta confirmada!!!", category="success")
        return redirect(url_for("auth.login"))
    else:
        flash("Token expirado", category="danger")
    return redirect(url_for("home.home_view"))


@auth_bp.route("/confirm")
@login_required
def resend_confirmation():
    token = current_user.get_confirm_token()
    send_email_confirm(current_user)
    flash("Email de confirmacion reenviado", category="info")
    return redirect(url_for("home.home_view"))
