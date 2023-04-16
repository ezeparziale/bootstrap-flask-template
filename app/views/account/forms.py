from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class AccountInfoForm(FlaskForm):
    firstname = StringField(label="Nombre")
    lastname = StringField(label="Apellido")
    username = StringField(label="Usuario")
    email = StringField(label="Email")
    picture = FileField(label="Foto de perfil")
    submit = SubmitField(label="Editar")


class AccountUpdateForm(FlaskForm):
    firstname = StringField(
        label="Nombre", validators=[DataRequired(), Length(min=3, max=20)]
    )
    lastname = StringField(
        label="Apellido", validators=[DataRequired(), Length(min=3, max=20)]
    )
    username = StringField(
        label="Usuario", validators=[DataRequired(), Length(min=3, max=20)]
    )
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    picture = FileField(
        label="Selecciona foto de perfil",
        validators=[FileAllowed(["jpg", "png"], "Images only!")],
    )
    submit = SubmitField(label="Actualizar")


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
