from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import db
from app.config import settings

from ...models import Participant, RoomMessage, User
from .forms import EmptyForm, ReplyMessageForm, SendMessageForm

user_bp = Blueprint(
    "user",
    __name__,
    url_prefix="/user",
    template_folder="templates",
    static_folder="static",
)


@user_bp.route("/<username>", methods=["GET", "POST"])
@login_required
def user(username: str):
    form = EmptyForm()
    user = db.one_or_404(db.select(User).filter_by(username=username))
    return render_template("user/user.html", user=user, form=form)


@user_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.one_or_404(db.select(User).filter_by(username=username))
        if user == current_user:
            flash("No te puede auto seguir", category="info")
            return redirect(url_for("user.user", username=username))
        if current_user.is_following(user):
            flash("Ya estás siguiendo a este usuario", category="info")
            return redirect(url_for("user.user", username=username))
        current_user.follow(user)
        flash(f"Estas siguiendo a {username}", category="success")
        return redirect(url_for("user.user", username=username))
    return render_template("user.user", username=username)


@user_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
        user = db.one_or_404(db.select(User).filter_by(username=username))
        if user == current_user:
            flash("No te puede auto seguir", category="info")
            return redirect(url_for("user.user", username=username))
        if not current_user.is_following(user):
            flash("No estás siguiendo a este usuario", category="info")
            return redirect(url_for("user.user", username=username))
        current_user.unfollow(user)
        flash(f"Ya no sigues a {username}", category="success")
        return redirect(url_for("user.user", username=username))
    return redirect(url_for("user.user", username=username))


@user_bp.route("/followers/<username>", methods=["GET"])
@login_required
def followers(username: str):
    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()

    if user is None:
        flash("Usuario invalido", category="info")
        return redirect(url_for("posts.posts", username=username))

    page = request.args.get("page", 1, type=int)
    per_page = settings.POSTS_PER_PAGE
    pagination = db.paginate(
        user.followers, page=page, per_page=per_page, error_out=False
    )

    return render_template("user/followers.html", pagination=pagination, user=user)


@user_bp.route("/follow_by/<username>", methods=["GET"])
@login_required
def follow_by(username: str):
    user = db.session.execute(db.select(User).filter_by(username=username)).scalar_one()

    if user is None:
        flash("Usuario invalido", category="info")
        return redirect(url_for("posts.posts", username=username))
    page = request.args.get("page", 1, type=int)

    per_page = settings.POSTS_PER_PAGE
    pagination = db.paginate(
        user.followed, page=page, per_page=per_page, error_out=False
    )

    return render_template("user/followed_by.html", pagination=pagination, user=user)


@user_bp.route("/notifications", methods=["GET"])
@login_required
def notifications():
    since = request.args.get("since", 0.0, type=float)
    notifications = current_user.get_notifications(since)
    return jsonify(
        [
            {"name": n.name, "data": n.get_data(), "timestamp": n.timestamp}
            for n in notifications
        ]
    )


@user_bp.route("/send_menssage_room/<username>", methods=["GET", "POST"])
@login_required
def send_menssage_room(username: str):
    recipient = db.one_or_404(db.select(User).filter_by(username=username))

    form = SendMessageForm()

    if form.validate_on_submit():
        message = form.message.data
        room_id = current_user.get_room_id(recipient)
        current_user.send_message_to_room(room_id, message)
        recipient.add_notification("unread_message_count", recipient.new_messages())
        return redirect(url_for("user.show_messages_room", room_id=room_id))

    return render_template(
        "user/send_message_room.html", form=form, recipient=recipient
    )


@user_bp.route("/show_messages_room/<room_id>", methods=["GET", "POST"])
@login_required
def show_messages_room(room_id: int):
    participant = db.one_or_404(
        db.select(Participant).filter(
            Participant.room_id == room_id, Participant.user_id == current_user.id
        )
    )

    form = ReplyMessageForm()
    if form.validate_on_submit():
        message = form.message.data
        current_user.send_message_to_room(room_id, message)
        participant.last_message_at = datetime.utcnow()
        form.message.data = ""

    participant.last_access_at = datetime.utcnow()
    db.session.commit()

    messages = (
        db.select(RoomMessage)
        .filter_by(room_id=room_id)
        .order_by(RoomMessage.created_at.desc())
    )
    page = request.args.get("page", 1, type=int)
    per_page = settings.POSTS_PER_PAGE
    pagination = db.paginate(messages, page=page, per_page=per_page, error_out=False)

    return render_template(
        "user/show_message_room.html",
        form=form,
        pagination=pagination,
        room_id=room_id,
    )


@user_bp.route("/show_rooms", methods=["GET", "POST"])
@login_required
def show_rooms():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)
    db.session.commit()

    subquery = db.select(Participant.room_id).filter_by(user_id=current_user.id)
    rooms = (
        db.select(Participant)
        .filter(
            Participant.room_id.in_(subquery), Participant.user_id != current_user.id
        )
        .order_by(Participant.created_at.desc())
    )

    page = request.args.get("page", 1, type=int)
    per_page = settings.POSTS_PER_PAGE
    pagination = db.paginate(rooms, page=page, per_page=per_page, error_out=False)

    return render_template(
        "user/show_rooms.html", pagination=pagination, current_user=current_user
    )
