from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, fresh_login_required, login_required
from .forms import AccountInfoForm, AccountUpdateForm
from app import db, app
import os
from app.auth.models import UserDetails

account_bp = Blueprint("account", __name__, url_prefix="/account", template_folder='templates')

def save_image(picture_file):
    picture_name = picture_file.filename
    picture_path = os.path.join(app.root_path, "static/img/profiles", picture_name)
    picture_file.save(picture_path)
    return picture_name


@account_bp.route("/", methods=["GET", "POST"])
@login_required
# @fresh_login_required
def account():
    form = AccountInfoForm()
    if form.validate_on_submit():
        return redirect(url_for("account.edit_account"))
    form.email.data = current_user.email
    form.username.data = current_user.username
    if current_user.details:
            form.firstname.data = current_user.details.firstname
            form.lastname.data = current_user.details.lastname
    image_url = url_for("static", filename="img/profiles/" + current_user.image_file)
    return render_template("account.html", form=form, image_url=image_url)
    

@account_bp.route("/edit", methods=["GET", "POST"])
@login_required
# @fresh_login_required
def edit_account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_image(form.picture.data)
            current_user.image_file = image_file

        current_user.username = form.username.data
        current_user.email = form.email.data

        if current_user.details:
            current_user.details.firstname=form.firstname.data
            current_user.details.lastname=form.lastname.data
        else:
            user_details = UserDetails(
                firstname=form.firstname.data, 
                lastname=form.lastname.data, 
                user_id=current_user.id)
            db.session.add(user_details)

        # current_user.details = user_details
        db.session.commit()
        flash(f"Cuenta actualizada", category="success")
        return redirect(url_for("account.account"))
    elif request.method=="GET":
        form.email.data = current_user.email
        form.username.data = current_user.username
        if current_user.details:
            form.firstname.data = current_user.details.firstname
            form.lastname.data = current_user.details.lastname
    image_url = url_for("static", filename="img/profiles/" + current_user.image_file)
    return render_template("edit_account.html", form=form, image_url=image_url)