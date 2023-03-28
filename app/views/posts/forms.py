from flask_wtf import FlaskForm
from wtforms import SelectMultipleField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length

from app import db

from ...models import Tag


class PostViewForm(FlaskForm):
    title = StringField(
        label="Titulo", validators=[DataRequired(), Length(min=5, max=40)]
    )
    content = TextAreaField(
        label="Contenido", validators=[DataRequired(), Length(min=10)]
    )


class PostForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.tags.choices = [
            (tag.id, tag.name) for tag in db.session.execute(db.select(Tag)).scalars()
        ]

    title = StringField(
        label="Titulo", validators=[DataRequired(), Length(min=5, max=40)]
    )
    content = TextAreaField(
        label="Contenido", validators=[DataRequired(), Length(min=10)]
    )
    tags = SelectMultipleField(
        label="Tags",
        validators=[DataRequired()],
        coerce=int,
        render_kw={"data-placeholder": "Seleccione una o más tags"},
    )


class CreatePostForm(PostForm):
    submit = SubmitField(label="Publicar")


class EditPostForm(PostForm):
    submit = SubmitField(label="Editar")


class PostCommentForm(FlaskForm):
    comment = TextAreaField(
        label="Comentario", validators=[DataRequired(), Length(min=10)]
    )
    submit = SubmitField(label="Comentar")
