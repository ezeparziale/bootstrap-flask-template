from app import db
from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.sqltypes import DateTime, TIMESTAMP
from sqlalchemy.sql.expression import text

class User(db.Model):
    id = Column(Integer, primary_key=True)
    username = Column(String(20), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    image_file = Column(String(), nullable=False, default="default.jpg")
    password = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text("CURRENT_TIMESTAMP"), nullable=False)

    def __repr__(self) -> str:
        return f"{self.username} : {self.email} : {self.created_at}"