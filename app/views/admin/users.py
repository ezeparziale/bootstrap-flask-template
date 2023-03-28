from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func, or_

from app import bcrypt, db
from app.decorators import admin_required
from app.models import User

from .forms import CreateUserForm, EditUserForm

users_bp = Blueprint(
    "users",
    __name__,
    url_prefix="/users",
    template_folder="templates",
    static_folder="static",
)


@users_bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def user_view():
    return render_template("users/list.html")


@users_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()

    if form.validate_on_submit():
        encrypted_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data,
            email=form.email.data,
            confirmed=form.confirmed.data,
            password=encrypted_password,
            image_file=User.generate_avatar(),
        )
        user.save()
        return redirect(url_for("admin.users.user_view"))

    return render_template("users/create.html", form=form)


@users_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(id):
    user = db.get_or_404(User, id)

    form = EditUserForm()

    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.confirmed = form.confirmed.data
        user.update()
        return redirect(url_for("admin.users.user_view"))

    form.id.data = user.id
    form.username.data = user.username
    form.email.data = user.email
    form.confirmed.data = user.confirmed

    return render_template("users/edit.html", form=form)


@users_bp.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def delete_user(id):
    user = db.get_or_404(User, id)
    user.delete()
    return redirect(url_for("admin.users.user_view"))


@users_bp.route("/get_data", methods=["GET"])
@login_required
@admin_required
def get_data():
    query = db.select(User)

    # search filter
    search = request.args.get("search[value]")
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f"%{search}%"),
                User.email.ilike(f"%{search}%"),
            )
        )
    total_filtered = db.session.execute(func.count(query.c["id"])).scalar_one()
    total_records = db.session.execute(
        func.count(db.select(User.id).c["id"])
    ).scalar_one()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f"order[{i}][column]")
        if col_index is None:
            break
        col_name = request.args.get(f"columns[{col_index}][data]")
        if col_name not in ["username"]:
            col_name = "username"
        descending = request.args.get(f"order[{i}][dir]") == "desc"
        col = getattr(User, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int)
    length = request.args.get("length", type=int)
    query = db.session.execute(query.offset(start).limit(length)).scalars()

    # response
    return {
        "data": [user.to_dict() for user in query],
        "recordsFiltered": total_filtered,
        "recordsTotal": total_records,
        "draw": request.args.get("draw", type=int),
    }
