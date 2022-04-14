from flask import Blueprint, redirect, render_template, url_for, flash, request
from .forms import PostForm, PostViewForm
from ..models import Post
from flask_login import current_user, login_required
from app import db

posts_bp = Blueprint("posts", __name__, url_prefix="/posts", template_folder='templates')

@posts_bp.route("/", methods=["GET", "POST"])
@login_required
def posts():
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
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template("posts.html", form=form, posts=posts)


@posts_bp.route("/<id>", methods=["GET"])
@login_required
def get_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    import pprint
    pprint.PrettyPrinter().pprint(id)
    form = PostViewForm()
    form.title.data = post.title
    form.content.data = post.content
    return render_template("post.html", form=form)