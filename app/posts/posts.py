from flask import Blueprint, abort, redirect, render_template, url_for, flash, request
from .forms import PostForm, PostViewForm
from ..models import Post
from flask_login import current_user, login_required
from app import db
from ..config import settings

posts_bp = Blueprint("posts", __name__, url_prefix="/posts", template_folder='templates')

@posts_bp.route("/", methods=["GET", "POST"])
@login_required
def posts():
    page = request.args.get("page", 1, type=int)
    pagination = Post.query.order_by(Post.created_at.desc()).paginate(page, settings.POSTS_PER_PAGE, error_out=True)

    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user
        )
        db.session.add(post)
        db.session.commit()
        flash("Post creado", category="success")
        return redirect(url_for("posts.posts"))

    posts = pagination.items
    return render_template("posts.html", form=form, posts=posts, pagination=pagination)


@posts_bp.route("/<id>", methods=["GET"])
@login_required
def get_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    form = PostViewForm()
    form.title.data = post.title
    form.content.data = post.content
    return render_template("post.html", form=form, post=post)

@posts_bp.route("/edit/<id>", methods=["GET","POST"])
@login_required
def edit_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if current_user != post.author:
        abort(404)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash("Post actualizado", category="success")
        return redirect(url_for("posts.posts"))
    form.title.data = post.title
    form.content.data = post.content
    return render_template("edit_post.html", form=form)

@posts_bp.route("/delete/<id>", methods=["GET","POST"])
@login_required
def delete_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if current_user != post.author:
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash("Post eliminado", category="success")
    return redirect(url_for("posts.posts"))