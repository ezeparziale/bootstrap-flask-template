from flask_wtf import FlaskForm
from sqlalchemy import and_
from wtforms import BooleanField, HiddenField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length, ValidationError

from app import db
from app.models import Tag, User


class CreateTagForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=30)])
    submit = SubmitField("Create")

    def validate_name(self, field):
        tag = (
            db.session.execute(db.select(Tag).filter_by(name=field.data))
            .scalars()
            .first()
        )
        if tag:
            raise ValidationError("Tag name already exists.")


class EditTagForm(FlaskForm):
    id = HiddenField()
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=30)])
    submit = SubmitField("Update")

    def validate_name(self, field):
        check_tag_exists = (
            db.session.execute(
                db.select(Tag).filter(
                    and_(Tag.name == field.data, Tag.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_tag_exists:
            raise ValidationError(f"Tag '{field.data}' already exists.")


class EditUserForm(FlaskForm):
    id = HiddenField()
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    confirmed = BooleanField("Confirmed", render_kw={"role":"switch"})
    submit = SubmitField("Update")

    def validate_username(self, field):
        check_username_exists = (
            db.session.execute(
                db.select(User).filter(
                    and_(User.username == field.data, User.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_username_exists:
            raise ValidationError(f"Username '{field.data}' already exists.")

    def validate_email(self, field):
        check_email_exists = (
            db.session.execute(
                db.select(User).filter(
                    and_(User.email == field.data, User.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_email_exists:
            raise ValidationError(f"Email '{field.data}' already exists.")


class CreateUserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=16)]
    )
    confirmed = BooleanField("Confirmed", render_kw={"role":"switch"})
    submit = SubmitField("Create")

    def validate_username(self, field):
        check_username_exists = (
            db.session.execute(
                db.select(User).filter(and_(User.username == field.data))
            )
            .scalars()
            .first()
        )

        if check_username_exists:
            raise ValidationError(f"Username '{field.data}' already exists.")

    def validate_email(self, field):
        check_email_exists = (
            db.session.execute(db.select(User).filter(and_(User.email == field.data)))
            .scalars()
            .first()
        )

        if check_email_exists:
            raise ValidationError(f"Email '{field.data}' already exists.")
