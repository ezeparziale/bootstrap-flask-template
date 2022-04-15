from flask import Blueprint, redirect, render_template, request, url_for, flash
from flask_login import current_user, fresh_login_required, login_required
from app import db, app
import os
from ..models import User

user_bp = Blueprint("user", __name__, url_prefix="/user", template_folder='templates')

@user_bp.route("/<username>", methods=["GET", "POST"])
@login_required
def user(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template("user.html", user=user)


@user_bp.route("/follow/<username>", methods=["GET"])
@login_required
def follow(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash("No te puede auto seguir", category="info")
        return redirect(url_for("user.user", username=username))
    current_user.follow(user)
    flash(f"Estas siguiendo a {username}", category="success")
    return redirect(url_for("user.user", username=username))


@user_bp.route("/unfollow/<username>", methods=["GET"])
@login_required
def unfollow(username: str):
    user = User.query.filter_by(username=username).first_or_404()
    if user == current_user:
        flash("No te puedes auto seguir", category="info")
        return redirect(url_for("user.user", username=username))
    current_user.unfollow(user)
    flash(f"Ya no sigues a {username}", category="success")
    return redirect(url_for("user.user", username=username))