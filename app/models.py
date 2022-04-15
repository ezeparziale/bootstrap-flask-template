from flask import current_app, redirect, url_for
from app import db, login_manager
from sqlalchemy import Column, Integer, String, BOOLEAN, ForeignKey, Text
from sqlalchemy.sql.sqltypes import DateTime, TIMESTAMP
from sqlalchemy.sql.expression import text
from flask_login import UserMixin
import jwt
from datetime import datetime, timedelta, timezone

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