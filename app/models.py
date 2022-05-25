from flask import current_app, redirect, url_for
from app import app, db, login_manager
from sqlalchemy import Column, Integer, String, BOOLEAN, ForeignKey, Text
from sqlalchemy.sql.sqltypes import DateTime, TIMESTAMP
from sqlalchemy.sql.expression import text
from flask_login import UserMixin, AnonymousUserMixin
import jwt
from datetime import datetime, timedelta, timezone
import random
import json

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))

class Follow(db.Model):
    __tablename__ = "follows"
    follower_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followed_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    followed_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"{self.user_id} {self.follower_id}"

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(40), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(), nullable=False, default="default.jpg")
    password = Column(String(60), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    confirmed = Column(BOOLEAN, default=False)
    last_seen = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    details = db.relationship("UserDetail", backref="user", lazy=True, uselist=False)
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    followed = db.relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        backref=db.backref("follower", lazy="joined"), 
        lazy="dynamic", 
        cascade="all, delete-orphan"
    )
    followers = db.relationship(
        "Follow", 
        foreign_keys=[Follow.followed_id],
        backref=db.backref("followed", lazy="joined"), 
        lazy="dynamic", 
        cascade="all, delete-orphan"
    )
    comments = db.relationship("Comment", backref="author", lazy="dynamic")
    rol_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    likes = db.relationship("Like", backref="user", lazy="dynamic")
    favorites = db.relationship("Favorite", backref="user", lazy="dynamic")
    # messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic")
    # messages_received = db.relationship("Message", foreign_keys="Message.recipient_id", backref="recipient", lazy="dynamic")
    last_message_read_time = db.Column(TIMESTAMP)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    views = db.relationship("View", backref="user", lazy="dynamic")
    report = db.relationship("Report", backref="user", lazy="dynamic")
    comments_reported = db.relationship("CommentReport", backref="user", lazy="dynamic")
    comments_liked = db.relationship("CommentLike", backref="user", lazy="dynamic")
    participant = db.relationship("Participant", backref="user", lazy="dynamic")
    room_messages = db.relationship("RoomMessage", backref="author", lazy="dynamic")

    @staticmethod
    def generate_avatar():
        return f"avatar{random.randint(0,14)}.png"

    # def send_message(self, recipient, message):
    #     msg = Message(sender_id=self.id, recipient_id=recipient.id, message=message)
    #     db.session.add(msg)
    #     db.session.commit()

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()

    def __repr__(self) -> str:
        return f"{self.username} : {self.email} : {self.created_at}"

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def get_token(self, expires_sec=300):
        encoded = jwt.encode({
            "user_id":self.id, 
            "exp":datetime.now(tz=timezone.utc) + timedelta(seconds=expires_sec)}, 
            current_app.config["SECRET_KEY"], 
            algorithm="HS256")
        return encoded

    def get_confirm_token(self, expires_sec=300):
        encoded = jwt.encode({
            "comfirm":self.id, 
            "exp":datetime.now(tz=timezone.utc) + timedelta(seconds=expires_sec)}, 
            current_app.config["SECRET_KEY"], 
            algorithm="HS256")
        return encoded

    def confirm(self, token):
        try:
            decode = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            if decode.get("comfirm") != self.id:
                return False
            self.confirmed = True
            db.session.commit()
            return True
        except: 
            return None

    @staticmethod
    def verify_token(token):
        try:
            decode = jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])
            user_id = decode.get("user_id")
        except: 
            return None
        return User.query.get(user_id)

    def follow(self, user):
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()
    
    def unfollow(self, user):
        follow = self.followed.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user):
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user):
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(Follow.follower_id == self.id)

    @property
    def favorites_posts(self):
        return Post.query.join(Favorite, Favorite.post_id == Post.id).filter(Favorite.user_id == self.id)
        
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self):
        return self.can(Permission.ADMIN)

    def is_moderate(self):
        return self.can(Permission.MODERATE)

    def add_notification(self, name, data):
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        db.session.commit()

    def new_messages(self):
        subquery = db.select([Participant.room_id]).filter_by(user_id=self.id)
        rooms = Participant.query.filter(Participant.room_id.in_(subquery), Participant.user_id!=self.id).order_by(Participant.created_at.desc())
        unread_messages = 0
        for room in rooms:
            unread_messages += self.get_room_messages(room.room_id)
        return unread_messages

    def get_notifications(self, since):
        return self.notifications.filter(Notification.timestamp > datetime.utcfromtimestamp(since)).order_by(Notification.timestamp.asc())

    def get_room_id(self, recipient):
        room_id = None
        for participate in self.participant:
            user_to_participant = Participant.query.filter(Participant.room_id==participate.room_id, Participant.user_id!=participate.user_id).first()
            user_to = User.query.filter(User.id==user_to_participant.user_id).first()
            if user_to.username == recipient.username:
                room_id = participate.room_id
                break

        if room_id is None:
            room = Room(name=f"{self.username}-{recipient.username}")
            db.session.add(room)
            db.session.commit()
            participant = Participant(user_id=self.id, room_id=room.id)
            db.session.add(participant)
            db.session.commit()
            participant = Participant(user_id=recipient.id, room_id=room.id)
            db.session.add(participant)
            db.session.commit()
            room_id = room.id

        return room_id

    def send_message_to_room(self, room_id, message):
        msg = RoomMessage(message=message, user_id=self.id, room_id=room_id)
        room = Room.query.filter_by(id=room_id).first()
        room.last_message_at = datetime.utcnow()
        db.session.add(msg)
        db.session.commit()

    def get_room_messages(self, room_id):
        participant = Participant.query.filter(Participant.room_id==room_id, Participant.user_id==self.id).first()
        room = Room.query.filter_by(id=room_id).first()
        messages = RoomMessage.query.filter(RoomMessage.room_id==room_id, RoomMessage.created_at>participant.last_access_at).order_by(RoomMessage.created_at.asc()).count()
        return messages


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm):
        return False

    def is_admin(self):
        return False

login_manager.anonymous_user = AnonymousUser

class UserDetail(db.Model):
    __tablename__ = "user_details"
    id = Column(Integer, primary_key=True)
    firstname = Column(String(60), unique=True, nullable=False)
    lastname = Column(String(60), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        return f"{self.firstname} {self.lastname}"

class PostTag(db.Model):
    __tablename__ = "post_tags"
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} post_id={self.post_id} tag_id={self.tag_id}"

class Tag(db.Model):
    __tablename__ = "tags"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    posts = db.relationship("PostTag", backref=db.backref("tag", remote_side=[id]), lazy="dynamic")

    def __repr__(self) -> str:
        return f"id={self.id} name={self.name}"

class Post(db.Model):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(60), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comments = db.relationship("Comment", backref="post", cascade="all, delete-orphan", lazy="dynamic")
    likes = db.relationship("Like", backref="post", cascade="all, delete-orphan", lazy="dynamic")
    favorites = db.relationship("Favorite", backref="post", cascade="all, delete-orphan", lazy="dynamic")
    views = db.relationship("View", backref="post", cascade="all, delete-orphan", lazy="dynamic")
    reports = db.relationship("Report", backref="post", cascade="all, delete-orphan", lazy="dynamic")
    closed = Column(BOOLEAN, default=False)
    disabled = Column(BOOLEAN, default=False)
    tags = db.relationship("PostTag", backref=db.backref("post", remote_side=[id]), lazy="dynamic")
    
    def add_visit(self):
        self.visits += 1
        db.session.commit()

    def if_favorite(self, user):
        return self.favorites.filter_by(user_id=user.id).first() is not None

    def favorite(self, user):
        if not self.if_favorite(user):
            favorite = Favorite(user=user, post=self)
            db.session.add(favorite)
            db.session.commit()

    def unfavorite(self, user):
        favorite = self.favorites.filter_by(user_id=user.id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()

    def is_like(self, user):
        return self.likes.filter_by(user_id=user.id).first() is not None

    def like(self, user):
        if not self.is_like(user):
            like = Like(user=user, post=self)
            db.session.add(like)
            db.session.commit()

    def unlike(self, user):
        like = self.likes.filter_by(user_id=user.id).first()
        if like:
            db.session.delete(like)
            db.session.commit()

    def get_views(self):
        return self.views.distinct(View.user_id).count()

    def add_view(self, user):
        view = View(user_id=user.id, post_id=self.id)
        db.session.add(view)
        db.session.commit()

    def add_report(self, user):
        report = Report(user_id=user.id, post_id=self.id)
        db.session.add(report)
        db.session.commit()

    def get_reports(self):
        return self.reports.distinct(Report.user_id).count()

    def delete_report(self, user):
        report = self.reports.filter_by(user_id=user.id).first()
        if report:
            db.session.delete(report)
            db.session.commit()
    
    def is_report(self, user):
        return self.reports.filter_by(user_id=user.id).first() is not None

    def is_reported(self):
        return self.reports.count() > 0

    def close(self):
        self.closed = True
        db.session.commit()

    def open(self):
        self.closed = False
        db.session.commit()

    def is_closed(self):
        return self.closed

    def is_disabled(self):
        return self.disabled


class Like(db.Model):
    __tablename__ = "likes"
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)


class Favorite(db.Model):
    __tablename__ = "favorites"
    id = Column(Integer, primary_key=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)

class Comment(db.Model):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    content = Column(Text, nullable=False)
    disabled = Column(BOOLEAN, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    childrens = db.relationship("Comment", backref=db.backref("parent", remote_side=[id]))
    level = Column(Integer, default=0)
    reports = db.relationship("CommentReport", backref="comment", cascade="all, delete-orphan", lazy="dynamic")
    likes = db.relationship("CommentLike", backref="comment", cascade="all, delete-orphan", lazy="dynamic")


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.parent:
            self.level = self.parent.level + 1

    def __repr__(self) -> str:
        return f"id={self.id} content={self.content}"

    def add_report(self, user):
        if not self.is_report(user):
            report = CommentReport(user_id=user.id, comment_id=self.id)
            db.session.add(report)
            db.session.commit()

    def delete_report(self, user):
        report = self.reports.filter_by(user_id=user.id).first()
        if report:
            db.session.delete(report)
            db.session.commit()

    def is_report(self, user):
        return self.reports.filter_by(user_id=user.id).first() is not None

    def is_reported(self):
        return self.reports.count() > 0

    def get_reports(self):
        return self.reports.distinct(CommentReport.user_id).count()

    def is_like(self, user):
        return self.likes.filter_by(user_id=user.id).first() is not None

    def like(self, user):
        if not self.is_like(user):
            like = CommentLike(user=user, comment=self)
            db.session.add(like)
            db.session.commit()

    def unlike(self, user):
        like = self.likes.filter_by(user_id=user.id).first()
        if like:
            db.session.delete(like)
            db.session.commit()

class Role(db.Model):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True)
    name = Column(String(40), unique=True, nullable=False)
    default = Column(BOOLEAN, default=False, index=True)
    permissions = Column(Integer, nullable=False)
    users = db.relationship("User", backref="role", lazy="dynamic")

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm
    
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm
    
    def reset_permissions(self):
        self.permissions = 0

    def has_permission(self, perm):
        return self.permissions & perm == perm

    def __repr__(self) -> str:
        return f"{self.name}"

    @staticmethod
    def insert_roles():
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE_POSTS],
            "Moderator": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE_POSTS, Permission.MODERATE],
            "Admin": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE_POSTS, Permission.MODERATE, Permission.ADMIN],
        }
        default_role = "User"
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = (role.name == default_role)
            db.session.add(role)
        db.session.commit()

class Permission:
    FOLLOW = 0x01
    COMMENT = 0x02
    WRITE_POSTS = 0x04
    MODERATE = 0x08
    ADMIN = 0x80

@app.context_processor
def inject_permission():
    return dict(Permission=Permission)


# class Message(db.Model):
#     __tablename__ = "messages"
#     id = Column(Integer, primary_key=True)
#     message = Column(Text, nullable=False)
#     created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
#     sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
#     read = Column(BOOLEAN, default=False)
#     parent_id = Column(Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=True)
#     childrens = db.relationship("Message", backref=db.backref("parent", remote_side=[id]), lazy="dynamic")
#     level = Column(Integer, default=0)
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         if self.parent:
#             self.level = self.parent.level + 1

#     def reply(self, message, sender_id, recipient_id):
#         if self.parent:
#             raise Exception("This message is already a reply")
            
#         reply = Message(message=message, parent=self, sender_id=sender_id, recipient_id=recipient_id)
#         reply.level = self.level + 1
#         db.session.add(reply)
#         db.session.commit()

class Notification(db.Model):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    payload_json = Column(Text, nullable=False)

    def get_data(self):
        return json.loads(str(self.payload_json))

class View(db.Model):
    __tablename__ = "views"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

class Report(db.Model):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    post_id = Column(Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

class CommentReport(db.Model):
    __tablename__ = "comment_reports"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} user_id={self.user_id} comment_id={self.comment_id}"

class CommentLike(db.Model):
    __tablename__ = "comment_likes"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comment_id = Column(Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} user_id={self.user_id} comment_id={self.comment_id}"

class Participant(db.Model):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    last_access_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    last_message_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} user_id={self.user_id} room_id={self.room_id}"

class Room(db.Model):
    __tablename__ = "rooms"
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    participants = db.relationship("Participant", backref=db.backref("room", remote_side=[id]), lazy="dynamic")
    messages = db.relationship("RoomMessage", backref=db.backref("room", remote_side=[id]), lazy="dynamic")
    last_message_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} name={self.name}"

class RoomMessage(db.Model):
    __tablename__ = "room_messages"
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        return f"id={self.id} message={self.message} user_id={self.user_id} room_id={self.room_id}"