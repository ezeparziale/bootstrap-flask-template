from datetime import datetime

from flask import (
    Blueprint,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.config import settings
from app.user.forms import EmptyForm, ReplyMessageForm, SendMessageForm

from ..models import Notification, Participant, RoomMessage, User

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
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user, form=form)


@user_bp.route("/follow/<username>", methods=["POST"])
@login_required
def follow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
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
    return render_template("user.user", username=username)


@user_bp.route("/unfollow/<username>", methods=["POST"])
@login_required
def unfollow(username: str):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first_or_404()
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
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash("Usuario invalido", category="info")
        return redirect(url_for("posts.posts", username=username))
    page = request.args.get("page", 1, type=int)
    pagination = user.followers.paginate(page, settings.POSTS_PER_PAGE, False)
    followers = pagination.items
    return render_template(
        "followers.html", followers=followers, pagination=pagination, user=user
    )


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
    return render_template(
        "followed_by.html", followed=followed, pagination=pagination, user=user
    )


# @user_bp.route("/send_message/<username>", methods=["GET", "POST"])
# @login_required
# def send_message(username: str):
#     recipient = User.query.filter_by(username=username).first_or_404()
#     form = SendMessageForm()
#     if form.validate_on_submit():
#         message = form.message.data
#         current_user.send_message(recipient, message)
#         recipient.add_notification("unread_message_count", recipient.new_messages())
#         flash("Mensaje enviado", category="success")
#         return redirect(url_for("user.show_messages_sent"))
#     return render_template("send_message.html", form=form, recipient=recipient)


# @user_bp.route("/messages", methods=["GET"])
# @login_required
# def messages():
#     current_user.last_message_read_time = datetime.utcnow()
#     current_user.add_notification("unread_message_count", 0)
#     db.session.commit()
#     view_message = 0
#     if current_user.is_authenticated:
#         view_message = int(request.cookies.get("view_message", 0))
#     if view_message == 0:
#         query = current_user.messages_received.filter(Message.level==0).order_by(Message.created_at.desc())
#     if view_message == 1:
#         query = current_user.messages_sent.filter(Message.level==0).order_by(Message.created_at.desc())

#     page = request.args.get("page", 1, type=int)
#     pagination = query.paginate(page, settings.POSTS_PER_PAGE, False)
#     messages = pagination.items
#     return render_template("messages.html", messages=messages, pagination=pagination, view_message=view_message)


# @user_bp.route("/show_messages_received", methods=["GET","POST"])
# @login_required
# def show_messages_received():
#     resp = make_response(redirect(url_for("user.messages")))
#     resp.set_cookie("view_message", "0", max_age=30*24*60*60) # 30 days
#     return resp

# @user_bp.route("/show_messages_sent", methods=["GET","POST"])
# @login_required
# def show_messages_sent():
#     resp = make_response(redirect(url_for("user.messages")))
#     resp.set_cookie("view_message", "1", max_age=30*24*60*60) # 30 days
#     return resp

# @user_bp.route("/view_message/<id>", methods=["GET", "POST"])
# @login_required
# def view_message(id: int):
#     message = Message.query.filter_by(id=id, level=0).first()
#     if message is None:
#         flash("Mensaje invalido", category="info")
#         return redirect(url_for("user.messages"))
#     if message.recipient != current_user and message.author != current_user:
#         flash("No puedes ver este mensaje", category="info")
#         return redirect(url_for("user.messages"))
#     message.read = True
#     db.session.commit()
#     form = ReplyMessageForm()
#     if form.validate_on_submit():
#         if current_user.id == message.sender_id:
#             sender_id = message.sender_id
#             recipient_id = message.recipient_id
#         else:
#             sender_id = message.recipient_id
#             recipient_id = message.sender_id
#         message.reply(form.message.data, sender_id, recipient_id)
#         flash("Respuesta enviada", category="success")
#         return redirect(url_for("user.view_message", id=message.id))

#     page = request.args.get("page", 1, type=int)
#     pagination = message.childrens.order_by(Message.created_at.desc()).paginate(page, settings.POSTS_PER_PAGE, error_out=True)

#     message_childrens = pagination.items

#     if current_user.id == message.sender_id:
#         message_type = "Enviados"
#     else:
#         message_type = "Recibidos"
#     return render_template("view_message.html", form=form, current_user=current_user, message=message, message_childrens=message_childrens, pagination=pagination, message_type=message_type)


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
    recipient = User.query.filter_by(username=username).first_or_404()

    form = SendMessageForm()

    if form.validate_on_submit():
        message = form.message.data
        room_id = current_user.get_room_id(recipient)
        current_user.send_message_to_room(room_id, message)
        recipient.add_notification("unread_message_count", recipient.new_messages())
        return redirect(url_for("user.show_messages_room", room_id=room_id))

    return render_template("send_message_room.html", form=form, recipient=recipient)


@user_bp.route("/show_messages_room/<room_id>", methods=["GET", "POST"])
@login_required
def show_messages_room(room_id: int):
    participant = Participant.query.filter(
        Participant.room_id == room_id, Participant.user_id == current_user.id
    ).first_or_404()
    if participant:
        form = ReplyMessageForm()
        if form.validate_on_submit():
            message = form.message.data
            current_user.send_message_to_room(room_id, message)
            participant.last_message_at = datetime.utcnow()

        participant.last_access_at = datetime.utcnow()
        db.session.commit()
        messages = RoomMessage.query.filter_by(room_id=room_id).order_by(
            RoomMessage.created_at.desc()
        )
        page = request.args.get("page", 1, type=int)
        pagination = messages.paginate(page, settings.POSTS_PER_PAGE, False)
        messages = pagination.items
        return render_template(
            "show_message_room.html",
            form=form,
            messages=messages,
            pagination=pagination,
            room_id=room_id,
        )
    else:
        abort(401)


@user_bp.route("/show_rooms", methods=["GET", "POST"])
@login_required
def show_rooms():
    current_user.last_message_read_time = datetime.utcnow()
    current_user.add_notification("unread_message_count", 0)
    db.session.commit()
    subquery = db.select([Participant.room_id]).filter_by(user_id=current_user.id)
    rooms = Participant.query.filter(
        Participant.room_id.in_(subquery), Participant.user_id != current_user.id
    ).order_by(Participant.created_at.desc())
    page = request.args.get("page", 1, type=int)
    pagination = rooms.paginate(page, settings.POSTS_PER_PAGE, False)
    rooms = pagination.items
    return render_template(
        "show_rooms.html", rooms=rooms, pagination=pagination, current_user=current_user
    )


@user_bp.route("/list_users", methods=["GET", "POST"])
@login_required
def list_users():
    query = User.query

    filters = None
    if request.method == "POST":
        filters = request.get_json()
        print(filters)
    if filters:
        if filters.get("confirmed"):
            query = query.filter_by(confirmed=filters.get("confirmed"))

    headers = ["username", "email", "confirmed"]

    page = request.args.get("page", 1, type=int)
    pagination = query.paginate(page, settings.POSTS_PER_PAGE, False)
    users = pagination.items

    print(pagination.total)
    return render_template(
        "list_users.html", users=users, headers=headers, pagination=pagination
    )


@user_bp.route("/api/data", methods=["GET", "POST"])
@login_required
def data():
    query = User.query

    # search filter
    search = request.args.get("search[value]")
    username_filter = request.args.get("columns[0][search][value]")
    print(request.args)
    print(username_filter)
    if username_filter:
        query = query.filter(User.username.regexp_match(f"{username_filter}"))
    if search:
        query = query.filter(
            db.or_(
                User.username.like(f"%{search}%"),
                User.email.like(f"%{search}%"),
            )
        )
    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f"order[{i}][column]")
        if col_index is None:
            break
        col_name = request.args.get(f"columns[{col_index}][data]")
        if col_name not in ["username", "email"]:
            col_name = "username"
        descending = request.args.get(f"order[{i}][dir]") == "desc"
        col = getattr(User, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int)
    length = request.args.get("length", type=int)
    query = query.offset(start).limit(length)

    # print(query.all())
    # response
    return {
        "data": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "confirmed": user.confirmed,
            }
            for user in query
        ],
        "recordsFiltered": total_filtered,
        "recordsTotal": User.query.count(),
        "draw": request.args.get("draw", type=int),
    }
