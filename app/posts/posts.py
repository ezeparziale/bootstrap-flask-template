from flask import Blueprint, abort, make_response, redirect, render_template, url_for, flash, request
from .forms import PostCommentForm, PostForm, PostViewForm
from ..models import Comment, Post
from flask_login import current_user, login_required
from app import db
from ..config import settings

posts_bp = Blueprint("posts", __name__, url_prefix="/posts", template_folder='templates')

@posts_bp.route("/", methods=["GET", "POST"])
@login_required
def posts():
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get("show_followed", ""))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    page = request.args.get("page", 1, type=int)
    pagination = query.order_by(Post.created_at.desc()).paginate(page, settings.POSTS_PER_PAGE, error_out=True)

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
    return render_template("posts.html", form=form, posts=posts, pagination=pagination, show_followed=show_followed)


@posts_bp.route("/<id>", methods=["GET", "POST"])
@login_required
def get_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    form = PostCommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.comment.data,
            author=current_user,
            post=post
        )
        db.session.add(comment)
        db.session.commit()
        flash("Comentario creado", category="success")
        return redirect(url_for("posts.get_post", id=id))
    
    page = request.args.get("page", 1, type=int)
    pagination = post.comments.order_by(Comment.created_at.desc()).paginate(page, settings.POSTS_PER_PAGE, error_out=True)

    comments = pagination.items
    return render_template("post.html", form=form, post=post, username=post.author.username, comments=comments, pagination=pagination)

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

@posts_bp.route("/show_all", methods=["GET","POST"])
@login_required
def show_all():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("show_followed", "", max_age=30*24*60*60) # 30 days
    return resp

@posts_bp.route("/show_followed", methods=["GET","POST"])
@login_required
def show_followed():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("show_followed", "1", max_age=30*24*60*60) # 30 days
    return resp