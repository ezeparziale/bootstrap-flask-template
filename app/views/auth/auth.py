import base64
import io

import pyotp
import qrcode
from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import (
    current_user,
    fresh_login_required,
    login_required,
    login_user,
    logout_user,
)

from app import settings
from app.utils.email import send_email

from ...models import DeletedUser, User
from .forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
    TwoFAForm,
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
        if current_user.blocked:
            logout_user()
            flash("Blocked account", category="info")


@auth_bp.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("home.home_view"))
    return render_template("auth/unconfirmed.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))

    session.pop("2fa_block", None)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            next = request.args.get("next")

            if user.is_blocked():
                flash("Blocked account", category="info")
            else:
                remember = form.remember_me.data
                if user.totp_enabled:
                    session["user_id"] = user.id
                    return redirect(
                        url_for("auth.verify_2fa", next=next, remember=remember)
                    )
                else:
                    user.handle_successful_login()
                    login_user(user, remember=remember)
                    if next is None or not next.startswith("/"):
                        next = url_for("home.home_view")
                    return redirect(next)
        else:
            if user:
                user.handle_failed_login()
            flash("Error al loguearse", category="danger")
    return render_template("auth/login.html", form=form)


def send_email_confirm(user):
    token = user.get_confirm_token()

    html_body = render_template(
        "auth/emails/confirm_account.html", token=token, app_name=settings.SITE_NAME
    )
    text_body = ""
    subject = "Confirm account"
    recipients = [user.email]
    sender = "noreplay@test.com"
    send_email(
        subject, sender, recipients, text_body, html_body, attachments=None, sync=False
    )


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.home_view"))

    form = RegistrationForm()

    if form.validate_on_submit():
        if DeletedUser.check_alredy_exists(
            username=form.username.data,
            email=form.email.data,
        ):
            flash("Username or Email are banned", category="info")
            return redirect(url_for("auth.register"))

        user = User(
            username=form.username.data,
            email=form.email.data,
            password_hash=User.generate_password_hash(form.password.data),
            image_file=User.generate_avatar(),
        )
        user.save()
        flash("Cuenta creada exitosamente", category="success")
        flash("Verifique su mail para confirmar cuenta", category="info")
        send_email_confirm(user)
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home.home_view"))


def send_email_reset_password(user):
    token = user.get_token()

    html_body = render_template(
        "auth/emails/reset_password.html", token=token, app_name=settings.SITE_NAME
    )
    text_body = ""
    subject = "Reset password"
    recipients = [user.email]
    sender = "noreplay@test.com"
    send_email(
        subject, sender, recipients, text_body, html_body, attachments=None, sync=False
    )


@auth_bp.route("/reset_password", methods=["GET", "POST"])
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
    return render_template("auth/reset_password.html", form=form)


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    user = User.verify_token(token)
    if user is None:
        flash("Token invalido", category="warning")
        return redirect(url_for("auth.reset_password"))

    form = ResetPasswordForm()
    print(form.data)
    if form.validate_on_submit():
        if user.verify_password_history(form.new_password.data):
            flash(
                "This password has been used before. Please choose a new one",
                category="danger",
            )
        else:
            user.set_password(form.new_password.data)
            flash("Password cambiado", category="success")
            return redirect(url_for("auth.login"))
    print("eze")
    return render_template("auth/change_password.html", form=form)


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
    send_email_confirm(current_user)
    flash("Email de confirmacion reenviado", category="info")
    return redirect(url_for("home.home_view"))


@auth_bp.route("/config_2fa", methods=["GET", "POST"])
@login_required
def config_2fa():
    if current_user.totp_enabled:
        return redirect(url_for("account.account"))

    form = TwoFAForm()

    if form.validate_on_submit():
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(form.token.data):
            flash("2FA enabled", category="success")
            current_user.enable_2fa()
            return redirect(url_for("home.home_view"))
        else:
            session["2fa_reset"] = session.get("2fa_reset", 0) + 1
            flash("Invalid token", category="danger")
            return redirect(url_for("auth.config_2fa"))

    if not current_user.totp_enabled:
        if session.get("2fa_reset", 0) == 3 or session.get("2fa_reset", None) is None:
            current_user.generate_token_2fa()
            session.pop("2fa_reset", None)

    img_data = generate_qr_code()
    return (
        render_template(
            "auth/config_2fa.html",
            form=form,
            img_data=img_data,
            secret=current_user.totp_secret,
        ),
        200,
        {
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
        },
    )


def generate_qr_code():
    totp = pyotp.TOTP(current_user.totp_secret)
    qr = qrcode.QRCode(version=1, box_size=7, border=2)
    qr.add_data(
        totp.provisioning_uri(name=current_user.email, issuer_name=settings.SITE_NAME)
    )
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_bytes = io.BytesIO()
    img.save(img_bytes)
    img_bytes.seek(0)
    encoded_img = base64.b64encode(img_bytes.read()).decode()

    return encoded_img


@auth_bp.route("/verify_2fa", methods=["GET", "POST"])
def verify_2fa():
    if current_user.is_authenticated:
        return redirect(url_for("account.account"))

    user_id = session.get("user_id", None)
    if not user_id:
        abort(401)

    form = TwoFAForm()

    next = request.args.get("next")
    remember = request.args.get("remember")

    if form.validate_on_submit():
        user = User.query.filter_by(id=user_id).first()
        totp = pyotp.TOTP(user.totp_secret)
        if totp.verify(form.token.data):
            session.pop("user_id", None)
            user.handle_successful_login()
            login_user(user, remember=remember)
            if next is None or not next.startswith("/"):
                next = url_for("home.home_view")
            return redirect(next)
        else:
            session["2fa_block"] = session.get("2fa_block", 0) + 1
            user.handle_failed_login()
            if session["2fa_block"] == 3:
                return redirect(url_for("auth.login", next=next, remember=remember))
            flash("Invalid token", category="danger")

        return redirect(url_for("auth.verify_2fa", next=next, remember=remember))

    return render_template("auth/verify_2fa.html", form=form)


@auth_bp.route("/disable_2fa", methods=["GET", "POST"])
@login_required
@fresh_login_required
def disable_2fa():
    current_user.disable_2fa()
    flash("Two factor authentication disabled", category="info")

    return redirect(url_for("account.account"))
