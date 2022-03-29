from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField


class AccountUpdateForm(FlaskForm):
    picture = FileField(label="Selecciona foto de perfil", validators=[FileRequired(), 
        FileAllowed(['jpg', 'png'], 'Images only!')])
    submit = SubmitField(label="Update account")
