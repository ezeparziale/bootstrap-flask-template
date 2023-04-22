from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length


class SendMessageForm(FlaskForm):
    message = TextAreaField(
        label="Message", validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField(label="Send")


class ReplyMessageForm(FlaskForm):
    message = TextAreaField(
        label="Message", validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField(label="Respond")


class EmptyForm(FlaskForm):
    submit = SubmitField(label="Respond")
