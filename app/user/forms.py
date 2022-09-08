from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class SendMessageForm(FlaskForm):
    message = TextAreaField(
        label="Mensaje", validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField(label="Enviar")


class ReplyMessageForm(FlaskForm):
    message = TextAreaField(
        label="Mensaje", validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField(label="Responder")


class EmptyForm(FlaskForm):
    submit = SubmitField(label="Reponder")
