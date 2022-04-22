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
    messages_sent = db.relationship("Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic")
    messages_received = db.relationship("Message", foreign_keys="Message.recipient_id", backref="recipient", lazy="dynamic")
    last_message_read_time = db.Column(TIMESTAMP)
    notifications = db.relationship("Notification", backref="user", lazy="dynamic")
    views = db.relationship("View", backref="user", lazy="dynamic")
    report = db.relationship("Report", backref="user", lazy="dynamic")

    @staticmethod
    def generate_avatar():
        img = []
        for i in range(1, 16):
            img.append(f"avatar{i}.png")
        return img[random.randint(0,14)]

    def send_message(self, recipient, message):
        msg = Message(sender_id=self.id, recipient_id=recipient.id, message=message)
        db.session.add(msg)
        db.session.commit()

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
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(Message.created_at > last_read_time).count()

    def get_notifications(self, since):
        return self.notifications.filter(Notification.timestamp > datetime.utcfromtimestamp(since)).order_by(Notification.timestamp.asc())


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


class Post(db.Model):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)
    title = Column(String(60), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    comments = db.relationship("Comment", backref="post", lazy="dynamic")
    likes = db.relationship("Like", backref="post", lazy="dynamic")
    favorites = db.relationship("Favorite", backref="post", lazy="dynamic")
    views = db.relationship("View", backref="post", lazy="dynamic")
    report = db.relationship("Report", backref="post", lazy="dynamic")

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
        return self.report.distinct(Report.user_id).count()

    def delete_report(self, user):
        report = self.report.filter_by(user_id=user.id).first()
        if report:
            db.session.delete(report)
            db.session.commit()
    
    def is_report(self, user):
        return self.report.filter_by(user_id=user.id).first() is not None


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


class Message(db.Model):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    read = Column(BOOLEAN, default=False)

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