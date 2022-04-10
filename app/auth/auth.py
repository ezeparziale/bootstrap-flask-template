from flask import Blueprint, redirect, render_template, url_for, flash, request
from .forms import RegistrationForm, LoginForm, ResetPasswordRequestForm, ResetPasswordForm
from .models import User
from app import db, bcrypt, mail, login_manager, app
from flask_login import login_required, login_user, logout_user, current_user
import pprint
from flask_mail import Message
from threading import Thread

auth_bp = Blueprint("auth", __name__, url_prefix="/auth", template_folder='templates')


@auth_bp.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.blueprint != 'auth' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth_bp.route('/unconfirmed/')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('home.home_view'))
    return render_template('unconfirmed.html')


@auth_bp.route("/login/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home.home_view'))
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


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)

def send_email_confirm(user):
    token = user.get_confirm_token()
    msg = Message(
        subject="Confirme cuenta", 
        recipients=[user.email],
        sender="noreplay@test.com"
    )
    msg.html = f"""
    <head>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">
    </head>
    <body>
        <p>Ingrese al siguiente link para confirmar cuenta:</p>
        <a class="btn btn-primary" href="{ url_for("auth.confirm", token=token, _external=True) }">Resetear Password</a>
    </body>
    """
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    pprint.PrettyPrinter().pprint(url_for("auth.reset_token", token=token, _external=True))
    return thr

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
        flash(f"Verifique su mail para confirmar cuenta", category="info")
        send_email_confirm(user)
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

    msg.html =render_template("email.html", token=token)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()    
    pprint.PrettyPrinter().pprint(url_for("auth.reset_token", token=token, _external=True))


@auth_bp.route("/reset_password/", methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_email(user)
            flash("Solicitud de reseteo de password enviada, revise su email", category="success")
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


@auth_bp.route("/confirm/<token>", methods=["GET", "POST"])
@login_required
def confirm(token):
    if current_user.confirmed:
        flash('La cuenta ya se encuentra confirmada', category="info")
        return redirect(url_for("home.home_view"))
    if current_user.confirm(token):
        flash("Cuenta confirmada!!!", category="success")
        return redirect(url_for("auth.login"))
    else:
        flash("Token expirado", category="danger")
    return redirect(url_for("home.home_view"))


@auth_bp.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.get_confirm_token()
    send_email_confirm(current_user)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for("home.home_view"))
