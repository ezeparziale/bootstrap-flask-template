from flask import Blueprint, abort, make_response, redirect, render_template, url_for, flash, request

from app.decorators import permission_required
from .forms import PostCommentForm, PostForm, PostViewForm
from ..models import Comment, Post, Permission
from flask_login import current_user, login_required
from app import db
from ..config import settings


posts_bp = Blueprint("posts", __name__, url_prefix="/posts", template_folder='templates')

@posts_bp.route("/", methods=["GET", "POST"])
@login_required
def posts():
    view_mode = 0
    if current_user.is_authenticated:
        view_mode = int(request.cookies.get("view_mode", 0))
    if view_mode == 0:
        query = Post.query
    if view_mode == 1:
        query = current_user.followed_posts
    if view_mode == 2:
        query = current_user.favorites_posts

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
    return render_template("posts.html", form=form, posts=posts, pagination=pagination, view_mode=view_mode)


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
    resp.set_cookie("view_mode", "0", max_age=30*24*60*60) # 30 days
    return resp

@posts_bp.route("/show_followed", methods=["GET","POST"])
@login_required
def show_followed():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("view_mode", "1", max_age=30*24*60*60) # 30 days
    return resp


@posts_bp.route("/show_favorite", methods=["GET","POST"])
@login_required
def show_favorite():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("view_mode", "2", max_age=30*24*60*60) # 30 days
    return resp

@posts_bp.route("/moderate/comment", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment():
    page = request.args.get("page", 1, type=int)
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(page, settings.POSTS_PER_PAGE, error_out=True)
    comments = pagination.items
    return render_template("moderate_comment.html", comments=comments, pagination=pagination)

@posts_bp.route("/moderate/comment/enable/<id>", methods=["GET","POST"])
@login_required
@permission_required(Permission.MODERATE)
def comment_enable(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    comment.disabled = False
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    flash("Comentario habilitado", category="success")
    return redirect(url_for("posts.moderate_comment", page=page))


@posts_bp.route("/moderate/comment/disable/<id>", methods=["GET","POST"])
@login_required
@permission_required(Permission.MODERATE)
def comment_disable(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    comment.disabled = True
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    flash("Comentario deshabilitado", category="success")
    return redirect(url_for("posts.moderate_comment", page=page))


@posts_bp.route("/like/<id>", methods=["GET","POST"])
@login_required
def like_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.like(current_user)
    flash("Post agregado a likes", category="success")
    return redirect(url_for("posts.get_post", id=id))

@posts_bp.route("/unlike/<id>", methods=["GET","POST"])
@login_required
def unlike_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.unlike(current_user)
    flash("Post eliminado de likes", category="success")
    return redirect(url_for("posts.get_post", id=id))

@posts_bp.route("/favorite/<id>", methods=["GET","POST"])
@login_required
def favorite_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.favorite(current_user)
    flash("Post agregado a favoritos", category="success")
    return redirect(url_for("posts.get_post", id=id))

@posts_bp.route("/unfavorite/<id>", methods=["GET","POST"])
@login_required
def unfavorite_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.unfavorite(current_user)
    flash("Post eliminado de favoritos", category="success")
    return redirect(url_for("posts.get_post", id=id))
