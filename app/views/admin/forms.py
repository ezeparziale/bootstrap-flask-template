from flask_wtf import FlaskForm
from sqlalchemy import and_
from wtforms import HiddenField, SelectMultipleField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError

from app.models import Tag


class CreateTagForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=30)])

    submit = SubmitField("Create")

    def validate_name(self, field):
        if Tag.query.filter_by(name=field.data).first():
            raise ValidationError("Tag name already exists.")


class EditTagForm(FlaskForm):
    id = HiddenField()
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=30)])

    submit = SubmitField("Update")

    def validate(self):
        rv = FlaskForm.validate(self)
        if not rv:
            return False

        check_tag_exists = Tag.query.filter(
            and_(Tag.name == self.name.data, Tag.id != self.id.data)
        ).all()

        if check_tag_exists:
            self.name.errors.append(f"Tag: '{self.name.data}' name already exists.")
            return False

        return True
