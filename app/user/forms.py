from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired, Length


class MessageForm(FlaskForm):
    message = TextAreaField(label="Mensaje", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField(label="Enviar")
