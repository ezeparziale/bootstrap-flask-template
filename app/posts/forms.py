from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField
from wtforms.validators import DataRequired, Length

class PostViewForm(FlaskForm):
    title = StringField(label="Titulo", validators=[DataRequired(), Length(min=5, max=40)])
    content = TextAreaField(label="Contenido", validators=[DataRequired(), Length(min=10)])

class PostForm(FlaskForm):
    title = StringField(label="Titulo", validators=[DataRequired(), Length(min=5, max=40)])
    content = TextAreaField(label="Contenido", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField(label="Postear")