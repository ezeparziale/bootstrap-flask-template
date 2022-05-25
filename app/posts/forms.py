from flask_wtf import FlaskForm
from wtforms import SubmitField, TextAreaField, StringField, SelectMultipleField
from wtforms.validators import DataRequired, Length
from ..models import Tag


class PostViewForm(FlaskForm):
    title = StringField(label="Titulo", validators=[DataRequired(), Length(min=5, max=40)])
    content = TextAreaField(label="Contenido", validators=[DataRequired(), Length(min=10)])

class PostForm(FlaskForm):
    title = StringField(label="Titulo", validators=[DataRequired(), Length(min=5, max=40)])
    content = TextAreaField(label="Contenido", validators=[DataRequired(), Length(min=10)])
    tags = SelectMultipleField(label="Tags", validators=[DataRequired()], choices=[(tag.id, tag.name) for tag in Tag.query.all()], coerce=int)

class CreatePostForm(PostForm):
    submit = SubmitField(label="Publicar")

class EditPostForm(PostForm):
    submit = SubmitField(label="Editar")

class PostCommentForm(FlaskForm):
    comment = TextAreaField(label="Comentario", validators=[DataRequired(), Length(min=10)])
    submit = SubmitField(label="Comentar")