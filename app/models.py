from flask import current_app, redirect, url_for
from app import db, login_manager
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

class User(db.Model, UserMixin):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(), nullable=False, default="default.jpg")
    password = Column(String(60), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    confirmed = Column(BOOLEAN, default=False)
    last_seen = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)
    details = db.relationship("UserDetail", backref="user", lazy=True, uselist=False)

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

class UserDetail(db.Model):
    __tablename__ = "user_details"
    id = Column(Integer, primary_key=True)
    firstname = Column(String(20), unique=True, nullable=False)
    lastname = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    def __repr__(self) -> str:
        return f"{self.firstname} {self.lastname}"