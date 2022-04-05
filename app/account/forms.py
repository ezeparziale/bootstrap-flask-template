from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo, Email


class AccountUpdateForm(FlaskForm):
    firstname = StringField(label="Nombre", validators=[DataRequired(), Length(min=3, max=20)])
    lastname = StringField(label="Apellido", validators=[DataRequired(), Length(min=3, max=20)])
    username = StringField(label="Usuario", validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField(label="Email", validators=[DataRequired(), Email()])
    picture = FileField(label="Selecciona foto de perfil", validators=[FileAllowed(["jpg", "png"], "Images only!")])
    submit = SubmitField(label="Update account")
