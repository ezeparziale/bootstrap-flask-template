from flask import redirect, url_for
from app import db, login_manager
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import DateTime, TIMESTAMP
from sqlalchemy.sql.expression import text
from flask_login import UserMixin

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)

@login_manager.unauthorized_handler
def unauthorized():
    return redirect(url_for("auth.login"))

class User(db.Model, UserMixin):
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(), nullable=False, default="default.jpg")
    password = Column(String(60), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"{self.username} : {self.email} : {self.created_at}"