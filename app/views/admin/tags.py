from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import or_

from app.decorators import admin_required
from app.models import Tag

from .forms import CreateTagForm, EditTagForm

tags_bp = Blueprint(
    "tags",
    __name__,
    url_prefix="/tags",
    template_folder="templates",
    static_folder="static",
)


@tags_bp.route("/", methods=["GET", "POST"])
@login_required
@admin_required
def tag_view():
    tags = Tag.query.all()
    return render_template("tags/list.html", tags=tags)


@tags_bp.route("/create", methods=["GET", "POST"])
@login_required
@admin_required
def create_tag():
    form = CreateTagForm()

    if form.validate_on_submit():
        tag = Tag(
            name=form.name.data,
        )
        tag.save()
        return redirect(url_for("admin.tags.tag_view"))

    return render_template("tags/create.html", form=form)


@tags_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_tag(id):
    role = Tag.query.get_or_404(id)
    form = EditTagForm()

    if form.validate_on_submit():
        role.name = form.name.data
        role.update()
        return redirect(url_for("admin.tags.tag_view"))

    form.id.data = role.id
    form.name.data = role.name
    return render_template("tags/edit.html", form=form)


@tags_bp.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def delete_tag(id):
    tag = Tag.query.get_or_404(id)
    tag.delete()
    return redirect(url_for("admin.tags.tag_view"))


@tags_bp.route("/get_data", methods=["GET"])
@login_required
@admin_required
def get_data():
    query = Tag.query

    # search filter
    search = request.args.get("search[value]")
    if search:
        query = query.filter(
            or_(
                Tag.name.like(f"%{search}%"),
            )
        )
    total_filtered = query.count()

    # sorting
    order = []
    i = 0
    while True:
        col_index = request.args.get(f"order[{i}][column]")
        if col_index is None:
            break
        col_name = request.args.get(f"columns[{col_index}][data]")
        if col_name not in ["name"]:
            col_name = "name"
        descending = request.args.get(f"order[{i}][dir]") == "desc"
        col = getattr(Tag, col_name)
        if descending:
            col = col.desc()
        order.append(col)
        i += 1
    if order:
        query = query.order_by(*order)

    # pagination
    start = request.args.get("start", type=int)
    length = request.args.get("length", type=int)
    query = query.offset(start).limit(length)

    # response
    return {
        "data": [tag.to_dict() for tag in query],
        "recordsFiltered": total_filtered,
        "recordsTotal": Tag.query.count(),
        "draw": request.args.get("draw", type=int),
    }
