import json
import random
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union

import jwt
from flask import current_app, redirect, request, url_for
from flask_login import AnonymousUserMixin, UserMixin
from sqlalchemy import BOOLEAN, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.expression import text
from sqlalchemy.sql.sqltypes import TIMESTAMP

from app import app, bcrypt, db, login_manager


@login_manager.user_loader
def load_user(user_id) -> Optional["User"]:
    return User.query.get(user_id)


@login_manager.unauthorized_handler
def unauthorized() -> redirect:
    return redirect(url_for("auth.login", next=request.path))


class Follow(db.Model):
    __tablename__ = "follows"

    follower_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followed_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    followed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Follow(follower_id={self.user_id}, followed_id={self.follower_id}, followed_at={self.followed_at})"


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    image_file: Mapped[str] = mapped_column(
        String(), nullable=False, default="default.jpg"
    )
    password: Mapped[str] = mapped_column(String(60), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    confirmed: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    last_seen: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    details: Mapped["UserDetail"] = relationship(
        backref="user", lazy=True, uselist=False
    )
    posts: Mapped[List["Post"]] = relationship("Post", backref="author", lazy="dynamic")
    followed: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys=[Follow.follower_id],
        backref=db.backref("follower", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    followers: Mapped[List["Follow"]] = relationship(
        "Follow",
        foreign_keys=[Follow.followed_id],
        backref=db.backref("followed", lazy="joined"),
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", backref="author", lazy="dynamic"
    )
    rol_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False
    )
    likes: Mapped[List["Like"]] = relationship("Like", backref="user", lazy="dynamic")
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite", backref="user", lazy="dynamic"
    )
    last_message_read_time: Mapped[datetime] = mapped_column(TIMESTAMP, nullable=True)
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", backref="user", lazy="dynamic"
    )
    views: Mapped[List["View"]] = relationship("View", backref="user", lazy="dynamic")
    report: Mapped[List["Report"]] = relationship(
        "Report", backref="user", lazy="dynamic"
    )
    comments_reported: Mapped[List["CommentReport"]] = relationship(
        "CommentReport", backref="user", lazy="dynamic"
    )
    comments_liked: Mapped[List["CommentLike"]] = relationship(
        "CommentLike", backref="user", lazy="dynamic"
    )
    participant: Mapped[List["Participant"]] = relationship(
        "Participant", backref="user", lazy="dynamic"
    )
    room_messages: Mapped[List["RoomMessage"]] = relationship(
        "RoomMessage", backref="author", lazy="dynamic"
    )

    def __init__(self, **kwargs) -> None:
        super(User, self).__init__(**kwargs)
        if self.role is None:
            self.role = Role.query.filter_by(default=True).first()

    def __repr__(self) -> str:
        return f"User(username={self.username}, email={self.email}, created_at={self.created_at})"

    @staticmethod
    def generate_avatar() -> str:
        return f"avatar{random.randint(1,15)}.png"

    def reset_avatar(self) -> None:
        self.image_file = User.generate_avatar()
        self.update()

    def ping(self) -> None:
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def get_token(self, expires_sec: int = 300) -> str:
        encoded = jwt.encode(
            {
                "user_id": self.id,
                "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_sec),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return encoded

    def get_confirm_token(self, expires_sec: int = 300) -> str:
        encoded = jwt.encode(
            {
                "comfirm": self.id,
                "exp": datetime.now(tz=timezone.utc) + timedelta(seconds=expires_sec),
            },
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        )
        return encoded

    def confirm(self, token: str) -> bool | None:
        try:
            decode = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            if decode.get("comfirm") != self.id:
                return False
            self.confirmed = True
            db.session.commit()
            return True
        except:
            return None

    @staticmethod
    def verify_token(token: str) -> Union["User", None]:
        try:
            decode = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )
            user_id = decode.get("user_id")
        except:
            return None
        return db.session.execute(db.select(User).filter_by(id=user_id)).scalar_one()

    def check_password(self, password: str) -> bool:
        return bcrypt.check_password_hash(self.password, password)

    def set_password(self, password: str) -> None:
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        self.update()

    @staticmethod
    def generate_password_hash(password: str) -> str:
        return bcrypt.generate_password_hash(password).decode("utf-8")

    def follow(self, user: "User") -> None:
        if not self.is_following(user):
            follow = Follow(follower=self, followed=user)
            db.session.add(follow)
            db.session.commit()

    def unfollow(self, user: "User") -> None:
        follow = self.followed.filter_by(followed_id=user.id).first()
        if follow:
            db.session.delete(follow)
            db.session.commit()

    def is_following(self, user: "User") -> bool:
        return self.followed.filter_by(followed_id=user.id).first() is not None

    def is_followed_by(self, user: "User") -> bool:
        return self.followers.filter_by(follower_id=user.id).first() is not None

    @property
    def followed_posts(self) -> Optional[List["Post"]]:
        return Post.query.join(Follow, Follow.followed_id == Post.author_id).filter(
            Follow.follower_id == self.id
        )

    @property
    def favorites_posts(self) -> Optional[List["Post"]]:
        return Post.query.join(Favorite, Favorite.post_id == Post.id).filter(
            Favorite.user_id == self.id
        )

    def can(self, perm: str) -> bool:
        return self.role is not None and self.role.has_permission(perm)

    def is_admin(self) -> bool:
        return self.can(Permission.ADMIN)

    def is_moderate(self) -> bool:
        return self.can(Permission.MODERATE)

    def add_notification(self, name: str, data: str) -> None:
        self.notifications.filter_by(name=name).delete()
        n = Notification(name=name, payload_json=json.dumps(data), user=self)
        db.session.add(n)
        db.session.commit()

    def new_messages(self) -> int:
        subquery = db.select(Participant.room_id).filter_by(user_id=self.id)
        rooms = Participant.query.filter(
            Participant.room_id.in_(subquery), Participant.user_id != self.id
        ).order_by(Participant.created_at.desc())
        unread_messages = 0
        for room in rooms:
            unread_messages += self.get_room_messages(room.room_id)
        return unread_messages

    def get_notifications(self, since: datetime) -> Optional["Notification"]:
        return self.notifications.filter(
            Notification.timestamp > datetime.utcfromtimestamp(since)
        ).order_by(Notification.timestamp.asc())

    def get_room_id(self, recipient: "User") -> int:
        room_id = None
        for participate in self.participant:
            user_to_participant = Participant.query.filter(
                Participant.room_id == participate.room_id,
                Participant.user_id != participate.user_id,
            ).first()
            user_to = User.query.filter(User.id == user_to_participant.user_id).first()
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

    def send_message_to_room(self, room_id: int, message: str) -> None:
        msg = RoomMessage(message=message, user_id=self.id, room_id=room_id)
        room = Room.query.filter_by(id=room_id).first()
        room.last_message_at = datetime.utcnow()
        db.session.add(msg)
        db.session.commit()

    def get_room_messages(self, room_id: int) -> Optional[List["RoomMessage"]]:
        participant = Participant.query.filter(
            Participant.room_id == room_id, Participant.user_id == self.id
        ).first()
        room = Room.query.filter_by(id=room_id).first()
        messages = (
            RoomMessage.query.filter(
                RoomMessage.room_id == room_id,
                RoomMessage.created_at > participant.last_access_at,
            )
            .order_by(RoomMessage.created_at.asc())
            .count()
        )
        return messages

    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

    def update(self) -> None:
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "confirmed": self.confirmed,
            "created_at": self.created_at,
        }


class AnonymousUser(AnonymousUserMixin):
    def can(self, perm: str) -> bool:
        return False

    def is_admin(self) -> bool:
        return False


login_manager.anonymous_user = AnonymousUser


class UserDetail(db.Model):
    __tablename__ = "user_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    firstname: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    lastname: Mapped[str] = mapped_column(String(60), unique=True, nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"UserDetail(id={self.id}, firstname={self.firstname}, lastname={self.lastname}, user_id={self.user_id})"


class PostTag(db.Model):
    __tablename__ = "post_tags"

    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"PostTag(post_id={self.post_id}, tag_id={self.tag_id}, created_at={self.created_at})"


class Tag(db.Model):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    posts: Mapped[List["PostTag"]] = relationship(
        "PostTag", backref=db.backref("tag", remote_side=[id]), lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"Tag(id={self.id}, name={self.name}, created_at={self.created_at})"

    def save(self) -> None:
        db.session.add(self)
        db.session.commit()

    def update(self) -> None:
        self.updated_at = datetime.utcnow()
        db.session.commit()

    def delete(self) -> None:
        db.session.delete(self)
        db.session.commit()

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at,
        }


class Post(db.Model):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(60), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    comments: Mapped[List["Comment"]] = relationship(
        "Comment", backref="post", cascade="all, delete-orphan", lazy="dynamic"
    )
    likes: Mapped[List["Like"]] = relationship(
        "Like", backref="post", cascade="all, delete-orphan", lazy="dynamic"
    )
    favorites: Mapped[List["Favorite"]] = relationship(
        "Favorite", backref="post", cascade="all, delete-orphan", lazy="dynamic"
    )
    views: Mapped[List["View"]] = relationship(
        "View", backref="post", cascade="all, delete-orphan", lazy="dynamic"
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report", backref="post", cascade="all, delete-orphan", lazy="dynamic"
    )
    closed: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    disabled: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    tags: Mapped[List["PostTag"]] = relationship(
        "PostTag",
        backref=db.backref("post", remote_side=[id]),
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        return f"Post(id={self.id}, title={self.title}, content={self.content}, created_at={self.created_at}, author_id={self.author_id})"

    def add_visit(self) -> None:
        self.visits += 1
        db.session.commit()

    def is_favorite(self, user: "User") -> bool:
        return self.favorites.filter_by(user_id=user.id).first() is not None

    def favorite(self, user: "User") -> None:
        if not self.is_favorite(user):
            favorite = Favorite(user=user, post=self)
            db.session.add(favorite)
            db.session.commit()

    def unfavorite(self, user: "User") -> None:
        favorite = self.favorites.filter_by(user_id=user.id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()

    def is_like(self, user: "User") -> bool:
        return self.likes.filter_by(user_id=user.id).first() is not None

    def like(self, user: "User") -> None:
        if not self.is_like(user):
            like = Like(user=user, post=self)
            db.session.add(like)
            db.session.commit()

    def unlike(self, user: "User") -> None:
        like = self.likes.filter_by(user_id=user.id).first()
        if like:
            db.session.delete(like)
            db.session.commit()

    def get_views(self) -> int:
        return self.views.distinct(View.user_id).count()

    def add_view(self, user: "User") -> None:
        view = View(user_id=user.id, post_id=self.id)
        db.session.add(view)
        db.session.commit()

    def add_report(self, user: "User") -> None:
        report = Report(user_id=user.id, post_id=self.id)
        db.session.add(report)
        db.session.commit()

    def get_reports(self) -> int:
        return self.reports.distinct(Report.user_id).count()

    def delete_report(self, user: "User") -> None:
        report = self.reports.filter_by(user_id=user.id).first()
        if report:
            db.session.delete(report)
            db.session.commit()

    def is_report(self, user: "User") -> bool:
        return self.reports.filter_by(user_id=user.id).first() is not None

    def is_reported(self) -> bool:
        return self.reports.count() > 0

    def close(self) -> None:
        self.closed = True
        db.session.commit()

    def open(self) -> None:
        self.closed = False
        db.session.commit()

    def is_closed(self) -> bool:
        return self.closed

    def is_disabled(self) -> bool:
        return self.disabled

    def enable(self) -> None:
        self.disabled = False
        db.session.commit()

    def disable(self) -> None:
        self.disabled = True
        db.session.commit()


class Like(db.Model):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"Like(id={self.id}, created_at={self.created_at}, user_id={self.user_id}, post_id={self.post_id})"


class Favorite(db.Model):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"Favorite(id={self.id}, created_at={self.created_at}, user_id={self.user_id}, post_id={self.post_id})"


class Comment(db.Model):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    disabled: Mapped[bool] = mapped_column(BOOLEAN, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    author_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    parent_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True
    )
    childrens: Mapped[List["Comment"]] = relationship(
        "Comment", backref=db.backref("parent", remote_side=[id])
    )
    level: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    reports: Mapped[List["CommentReport"]] = relationship(
        "CommentReport", backref="comment", cascade="all, delete-orphan", lazy="dynamic"
    )
    likes: Mapped[List["CommentLike"]] = relationship(
        "CommentLike", backref="comment", cascade="all, delete-orphan", lazy="dynamic"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.parent:
            self.level = self.parent.level + 1

    def __repr__(self) -> str:
        return f"Comment(id={self.id}, content={self.content}, disabled={self.disabled}, created_at={self.created_at}, post_id={self.post_id}, author_id={self.author_id}, parent_id={self.parent_id})"

    def add_report(self, user: "User") -> None:
        if not self.is_report(user):
            report = CommentReport(user_id=user.id, comment_id=self.id)
            db.session.add(report)
            db.session.commit()

    def delete_report(self, user: "User") -> None:
        report = self.reports.filter_by(user_id=user.id).first()
        if report:
            db.session.delete(report)
            db.session.commit()

    def is_report(self, user: "User") -> bool:
        return self.reports.filter_by(user_id=user.id).first() is not None

    def is_reported(self) -> bool:
        return self.reports.count() > 0

    def get_reports(self) -> int:
        return self.reports.distinct(CommentReport.user_id).count()

    def is_like(self, user: "User") -> bool:
        return self.likes.filter_by(user_id=user.id).first() is not None

    def like(self, user: "User") -> None:
        if not self.is_like(user):
            like = CommentLike(user=user, comment=self)
            db.session.add(like)
            db.session.commit()

    def unlike(self, user: "User") -> None:
        like = self.likes.filter_by(user_id=user.id).first()
        if like:
            db.session.delete(like)
            db.session.commit()

    def disable(self) -> None:
        self.disabled = True
        db.session.commit()

    def enable(self) -> None:
        self.disabled = False
        db.session.commit()


class Role(db.Model):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(40), unique=True, nullable=False)
    default: Mapped[bool] = mapped_column(
        BOOLEAN, default=False, index=True, nullable=False
    )
    permissions: Mapped[int] = mapped_column(Integer, nullable=False)
    users: Mapped[List["User"]] = relationship("User", backref="role", lazy="dynamic")

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    def add_permission(self, perm: str) -> None:
        if not self.has_permission(perm):
            self.permissions += perm

    def remove_permission(self, perm: str) -> None:
        if self.has_permission(perm):
            self.permissions -= perm

    def reset_permissions(self) -> None:
        self.permissions = 0

    def has_permission(self, perm: str) -> bool:
        return self.permissions & perm == perm

    def __repr__(self) -> str:
        return f"Role(id={self.id}, name={self.name}, default={self.default}, permissions={self.permissions})"

    @staticmethod
    def insert_roles():
        roles = {
            "User": [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE_POSTS],
            "Moderator": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE_POSTS,
                Permission.MODERATE,
            ],
            "Admin": [
                Permission.FOLLOW,
                Permission.COMMENT,
                Permission.WRITE_POSTS,
                Permission.MODERATE,
                Permission.ADMIN,
            ],
        }
        default_role = "User"
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.reset_permissions()
            for perm in roles[r]:
                role.add_permission(perm)
            role.default = role.name == default_role
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


class Notification(db.Model):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    timestamp: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)

    def get_data(self) -> dict:
        return json.loads(str(self.payload_json))

    def __repr__(self) -> str:
        return f"Notification(id={self.id}, name={self.name}, post_id={self.post_id}, timestamp={self.timestamp}, payload_json={self.payload_json})"


class View(db.Model):
    __tablename__ = "views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"View(id={self.id}, user_id={self.user_id}, post_id={self.post_id}, created_at={self.created_at})"


class Report(db.Model):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    post_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("posts.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Report(id={self.id}, user_id={self.user_id}, post_id={self.post_id}, created_at={self.created_at})"


class CommentReport(db.Model):
    __tablename__ = "comment_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"CommentReport(id={self.id}, user_id={self.user_id}, comment_id={self.comment_id}, created_at={self.created_at})"


class CommentLike(db.Model):
    __tablename__ = "comment_likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    comment_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("comments.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"CommentLike(id={self.id}, user_id={self.user_id}, comment_id={self.comment_id}, created_at={self.created_at})"


class Participant(db.Model):
    __tablename__ = "participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    last_access_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    last_message_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Participant(id={self.id}, user_id={self.user_id}, room_id={self.room_id}, created_at={self.created_at}, last_access_at={self.last_access_at}, last_message_at={self.last_message_at})"


class Room(db.Model):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[int] = mapped_column(String(128), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    participants: Mapped[List["Participant"]] = relationship(
        "Participant", backref=db.backref("room", remote_side=[id]), lazy="dynamic"
    )
    messages: Mapped[List["RoomMessage"]] = relationship(
        "RoomMessage", backref=db.backref("room", remote_side=[id]), lazy="dynamic"
    )
    last_message_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Room(id={self.id},name={self.name}, created_at={self.created_at}, last_message_at={self.last_message_at}"


class RoomMessage(db.Model):
    __tablename__ = "room_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"id={self.id} message={self.message}, created_at={self.created_at}, user_id={self.user_id} room_id={self.room_id}"
