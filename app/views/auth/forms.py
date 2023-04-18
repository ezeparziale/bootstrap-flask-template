from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError

from app.models import User


class RegistrationForm(FlaskForm):
    username = StringField(
        label="Username", validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=16)]
    )
    confirm_password = PasswordField(
        label="Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField(label="Register")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("This username is already registered")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("This email address is already registered")


class LoginForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=16)]
    )
    remember_me = BooleanField(label="Remember me")
    submit = SubmitField(label="Login")


class ResetPasswordRequestForm(FlaskForm):
    email = EmailField(label="Email", validators=[DataRequired(), Email()])
    submit = SubmitField(label="Reset Password")


class ResetPasswordForm(FlaskForm):
    new_password = PasswordField(
        label="Password", validators=[DataRequired(), Length(min=6, max=16)]
    )
    confirm_password = PasswordField(
        label="Confirm Password",
        validators=[DataRequired(), EqualTo("new_password", "Passwords must match")],
    )
    submit = SubmitField(label="Change Password")


class TwoFAForm(FlaskForm):
    token = StringField(label="Code", validators=[DataRequired(), Length(min=6, max=6)])
    submit = SubmitField(label="Verify")
