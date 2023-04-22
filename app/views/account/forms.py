from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class AccountInfoForm(FlaskForm):
    firstname = StringField(label="First name")
    lastname = StringField(label="Last name")
    username = StringField(label="Username")
    email = StringField(label="Email")
    picture = FileField(label="Profile picture")
    submit = SubmitField(label="Edit")


class AccountUpdateForm(FlaskForm):
    firstname = StringField(
        label="First name", validators=[DataRequired(), Length(min=3, max=20)]
    )
    lastname = StringField(
        label="Last name", validators=[DataRequired(), Length(min=3, max=20)]
    )
    username = StringField(
        label="Username", validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    picture = FileField(
        label="Choose a profile picture",
        validators=[FileAllowed(["jpg", "png"], "Images only!")],
    )
    submit = SubmitField(label="Update")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Current Password", validators=[DataRequired()])
    new_password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
        ],
    )
    confirm_password = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("new_password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Save")


class DeleteAccountForm(FlaskForm):
    confirm_delete = BooleanField("I confirm that I want to delete my account")
    submit = SubmitField("Delete Account")
