from flask import Blueprint, make_response, redirect, render_template, request, url_for, flash
from flask_login import current_user, login_required
from app.config import settings
from app.user.forms import MessageForm
from ..models import Message, User
from app import db

user_bp = Blueprint("user", __name__, url_prefix="/user", template_folder='templates')

@user_bp.route("/<username>", methods=["GET", "POST"])
@login_required
def user(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user)


@user_bp.route("/follow/<username>", methods=["GET"])
@login_required
def follow(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash("No te puede auto seguir", category="info")
        return redirect(url_for("user.user", username=username))
    if current_user.is_following(user):
        flash("Ya estás siguiendo a este usuario", category="info")
        return redirect(url_for("user.user", username=username))
    current_user.follow(user)
    flash(f"Estas siguiendo a {username}", category="success")
    return redirect(url_for("user.user", username=username))


@user_bp.route("/unfollow/<username>", methods=["GET"])
@login_required
def unfollow(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash("No te puedes auto seguir", category="info")
        return redirect(url_for("user.user", username=username))
    if not current_user.is_following(user):
        flash("No estás siguiendo a este usuario", category="info")
        return redirect(url_for("user.user", username=username))
    current_user.unfollow(user)
    flash(f"Ya no sigues a {username}", category="success")
    return redirect(url_for("user.user", username=username))


@user_bp.route("/followers/<username>", methods=["GET"])
@login_required
def followers(username: str):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("Usuario invalido", category="info")
        return redirect(url_for("posts.posts", username=username))
    page = request.args.get("page", 1, type=int)
    pagination = user.followers.paginate(page, settings.POSTS_PER_PAGE, False)
    followers = pagination.items
    return render_template("followers.html", followers=followers, pagination=pagination, user=user)

@user_bp.route("/follow_by/<username>", methods=["GET"])
@login_required
def follow_by(username: str):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("Usuario invalido", category="info")
        return redirect(url_for("posts.posts", username=username))
    page = request.args.get("page", 1, type=int)
    pagination = user.followed.paginate(page, settings.POSTS_PER_PAGE, False)
    followed = pagination.items
    return render_template("followed_by.html", followed=followed, pagination=pagination, user=user)


@user_bp.route("/send_message/<username>", methods=["GET", "POST"])
@login_required
def send_message(username: str):
    recipient = User.query.filter_by(username=username).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        message = form.message.data
        current_user.send_message(recipient, message)
        flash("Mensaje enviado", category="success")
        return redirect(url_for("user.show_messages_sent"))
    return render_template("send_message.html", form=form, recipient=recipient)


@user_bp.route("/messages", methods=["GET"])
@login_required
def messages():
    view_message = 0
    if current_user.is_authenticated:
        view_message = int(request.cookies.get("view_message", 0))
    if view_message == 0:
        query = current_user.messages_received.order_by(Message.created_at.desc())
    if view_message == 1:
        query = current_user.messages_sent.order_by(Message.created_at.desc())

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page, settings.POSTS_PER_PAGE, False)
    messages = pagination.items
    return render_template("messages.html", messages=messages, pagination=pagination, view_message=view_message)


@user_bp.route("/show_messages_received", methods=["GET","POST"])
@login_required
def show_messages_received():
    resp = make_response(redirect(url_for("user.messages")))
    resp.set_cookie("view_message", "0", max_age=30*24*60*60) # 30 days
    return resp

@user_bp.route("/show_messages_sent", methods=["GET","POST"])
@login_required
def show_messages_sent():
    resp = make_response(redirect(url_for("user.messages")))
    resp.set_cookie("view_message", "1", max_age=30*24*60*60) # 30 days
    return resp

@user_bp.route("/view_message/<id>", methods=["GET"])
@login_required
def view_message(id: int):
    message = Message.query.get_or_404(id)
    if message.recipient != current_user and message.author != current_user:
        flash("No puedes ver este mensaje", category="info")
        return redirect(url_for("user.messages"))
    message.read = True
    db.session.commit()
    return render_template("view_message.html", message=message)