import email
from click import password_option
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Email

class RegistrationForm(FlaskForm):
    username = StringField(label="Username", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=6, max=16)])
    confirm_password = PasswordField(label="Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField(label="Sign Up")

class LoginForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=6, max=16)])
    remember_me = BooleanField(label="Remember me")
    submit = SubmitField(label="Login")

class ResetPasswordRequestForm(FlaskForm):
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    submit = SubmitField(label="Reset password")

class ResetPasswordForm(FlaskForm):
    password = PasswordField(label="Password", validators=[DataRequired(), Length(min=6, max=16)])
    confirm_password = PasswordField(label="Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField(label="Change Password")
