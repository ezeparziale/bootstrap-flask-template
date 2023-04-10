import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app import app, db
from app.decorators import password_not_expired

from ...models import UserDetail
from .forms import AccountInfoForm, AccountUpdateForm, ChangePasswordForm

account_bp = Blueprint(
    "account",
    __name__,
    url_prefix="/account",
    template_folder="templates",
    static_folder="static",
)


def save_image(picture_file):
    picture_name = picture_file.filename
    picture_path = os.path.join(
        app.root_path, "static/img/avatars/profiles", picture_name
    )
    picture_file.save(picture_path)
    return picture_name


@account_bp.route("/", methods=["GET", "POST"])
@login_required
@password_not_expired
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
    image_url = url_for("static", filename="img/avatars/" + current_user.image_file)
    return render_template("account/account.html", form=form, image_url=image_url)


@account_bp.route("/edit", methods=["GET", "POST"])
@login_required
@password_not_expired
# @fresh_login_required
def edit_account():
    form = AccountUpdateForm()
    if form.validate_on_submit():
        if form.picture.data:
            image_file = save_image(form.picture.data)
            current_user.image_file = "profiles/" + image_file

        current_user.username = form.username.data
        current_user.email = form.email.data

        if current_user.details:
            current_user.details.firstname = form.firstname.data
            current_user.details.lastname = form.lastname.data
        else:
            user_details = UserDetail(
                firstname=form.firstname.data,
                lastname=form.lastname.data,
                user_id=current_user.id,
            )
            db.session.add(user_details)

        # current_user.details = user_details
        db.session.commit()
        flash("Cuenta actualizada", category="success")
        return redirect(url_for("account.account"))
    elif request.method == "GET":
        form.email.data = current_user.email
        form.username.data = current_user.username
        if current_user.details:
            form.firstname.data = current_user.details.firstname
            form.lastname.data = current_user.details.lastname
    image_url = url_for("static", filename="img/avatars/" + current_user.image_file)
    return render_template("account/edit_account.html", form=form, image_url=image_url)


@account_bp.route("/reset_avatar")
@login_required
@password_not_expired
def reset_avatar():
    current_user.reset_avatar()
    return jsonify(
        {
            "status": True,
            "image_file": url_for(
                "static", filename="img/avatars/" + current_user.image_file
            ),
        }
    )


@account_bp.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.check_password(form.current_password.data):
            if current_user.verify_password_history(form.new_password.data):
                flash(
                    "This password has been used before. Please choose a new one",
                    category="danger",
                )
            else:
                current_user.set_password(form.new_password.data)
                flash("Your password has been changed", category="success")
                return redirect(url_for("account.account"))
        else:
            flash("Invalid current password", category="danger")
    return render_template("account/change_password.html", form=form)
