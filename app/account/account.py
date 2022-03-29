from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required
from .forms import AccountUpdateForm
from app import db, app
import os

account_bp = Blueprint("account", __name__, url_prefix="/account", template_folder='templates')

def save_image(picture_file):
    picture_name = picture_file.filename
    picture_path = os.path.join(app.root_path, "static/img/profiles", picture_name)
    picture_file.save(picture_path)
    return picture_name

@account_bp.route("/", methods=["GET", "POST"])
@login_required
def account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        image_file = save_image(form.picture.data)
        current_user.image_file = image_file
        db.session.commit()
        return redirect(url_for("account.account"))
    image_url = url_for("static", filename="img/profiles/" + current_user.image_file)
    return render_template("account.html", form=form, image_url=image_url)