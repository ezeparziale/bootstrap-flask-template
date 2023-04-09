from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy import func

from app import db
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
    return render_template("admin/tags/list.html")


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

    return render_template("admin/tags/create.html", form=form)


@tags_bp.route("/edit/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def edit_tag(id):
    tag = db.get_or_404(Tag, id)

    form = EditTagForm()

    if form.validate_on_submit():
        tag.name = form.name.data
        tag.update()
        return redirect(url_for("admin.tags.tag_view"))

    form.id.data = tag.id
    form.name.data = tag.name
    return render_template("admin/tags/edit.html", form=form)


@tags_bp.route("/delete/<int:id>", methods=["GET", "POST"])
@login_required
@admin_required
def delete_tag(id):
    tag = db.get_or_404(Tag, id)
    tag.delete()
    return redirect(url_for("admin.tags.tag_view"))


@tags_bp.route("/get_data", methods=["GET"])
@login_required
@admin_required
def get_data():
    query = db.select(Tag)

    # search filter
    search = request.args.get("search[value]")
    if search:
        query = query.filter(
            Tag.name.like(f"%{search}%"),
        )
    total_filtered = db.session.execute(func.count(query.c["id"])).scalar_one()
    total_records = db.session.execute(
        func.count(db.select(Tag.id).c["id"])
    ).scalar_one()

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
    query = db.session.execute(query.offset(start).limit(length)).scalars()

    # response
    return {
        "data": [tag.to_dict() for tag in query],
        "recordsFiltered": total_filtered,
        "recordsTotal": total_records,
        "draw": request.args.get("draw", type=int),
    }
