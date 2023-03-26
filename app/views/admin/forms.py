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

    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        check_tag_exists = (
            db.session.execute(
                db.select(Tag).filter(
                    and_(Tag.name == self.name.data, Tag.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_tag_exists:
            self.name.errors.append(f"Tag: '{self.name.data}' name already exists.")
            return False

        return True


class EditUserForm(FlaskForm):
    id = HiddenField()
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    confirmed = BooleanField("Confirmed")
    submit = SubmitField("Update")

    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        check_username_exists = (
            db.session.execute(
                db.select(User).filter(
                    and_(User.username == self.username.data, User.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_username_exists:
            self.username.errors.append(
                f"Username '{self.username.data}' already exists."
            )
            return False

        check_email_exists = (
            db.session.execute(
                db.select(User).filter(
                    and_(User.email == self.email.data, User.id != self.id.data)
                )
            )
            .scalars()
            .first()
        )

        if check_email_exists:
            self.email.errors.append(f"Email '{self.email.data}' already exists.")
            return False

        return True


class CreateUserForm(FlaskForm):
    username = StringField(
        "Username", validators=[DataRequired(), Length(min=2, max=30)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        label="PASSWORD", validators=[DataRequired(), Length(min=6, max=16)]
    )
    confirmed = BooleanField("Confirmed")
    submit = SubmitField("Create")

    def validate(self, extra_validators=None):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        check_username_exists = (
            db.session.execute(
                db.select(User).filter(and_(User.username == self.username.data))
            )
            .scalars()
            .first()
        )

        if check_username_exists:
            self.username.errors.append(
                f"Username '{self.username.data}' already exists."
            )
            return False

        check_email_exists = (
            db.session.execute(
                db.select(User).filter(and_(User.email == self.email.data))
            )
            .scalars()
            .first()
        )

        if check_email_exists:
            self.email.errors.append(f"Email '{self.email.data}' already exists.")
            return False

        return True
