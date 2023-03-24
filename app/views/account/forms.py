from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email, Length


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
