from flask import (
    Blueprint,
    abort,
    flash,
    make_response,
    redirect,
    render_template,
    request,
    url_for,
    jsonify
)
from flask_login import current_user, login_required

from app import db
from app.decorators import permission_required

from app.config import settings
from ...models import Comment, Permission, Post, PostTag, Report
from .forms import CreatePostForm, EditPostForm, PostCommentForm

posts_bp = Blueprint(
    "posts",
    __name__,
    url_prefix="/posts",
    template_folder="templates",
    static_folder="static",
)


@posts_bp.route("/", methods=["GET"])
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
    pagination = query.order_by(Post.created_at.desc()).paginate(
        page, settings.POSTS_PER_PAGE, error_out=True
    )
    posts = pagination.items
    return render_template(
        "posts.html", posts=posts, pagination=pagination, view_mode=view_mode
    )


@posts_bp.route("/<id>", methods=["GET", "POST"])
@login_required
def get_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    form = PostCommentForm()
    if form.validate_on_submit():
        comment = Comment(content=form.comment.data, author=current_user, post=post)
        db.session.add(comment)
        db.session.commit()
        # flash("Comentario creado", category="success")
        return redirect(url_for("posts.get_post", id=id))

    page = request.args.get("page", 1, type=int)
    pagination = (
        post.comments.filter_by(parent_id=None)
        .order_by(Comment.created_at.desc())
        .paginate(page, settings.POSTS_PER_PAGE, error_out=True)
    )

    comments = pagination.items
    post.add_view(current_user)
    return render_template(
        "post.html",
        form=form,
        post=post,
        username=post.author.username,
        comments=comments,
        pagination=pagination,
    )


@posts_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_post():
    form = CreatePostForm()
    print(form.tags.data)
    print(form.content.data)
    print(form.title.data)
    if form.validate_on_submit():

        post = Post(
            title=form.title.data, content=form.content.data, author=current_user
        )
        db.session.add(post)
        db.session.commit()

        for tag in form.tags.data:
            post_tags = PostTag(post_id=post.id, tag_id=tag)
            db.session.add(post_tags)

        db.session.commit()

        flash("Post creado", category="success")
        return redirect(url_for("posts.get_post", id=post.id))
    return render_template("create_post.html", form=form)


@posts_bp.route("/edit/<post_id>", methods=["GET", "POST"])
@login_required
def edit_post(post_id: int):
    post = Post.query.filter_by(id=post_id).first_or_404()
    if current_user != post.author and not current_user.is_admin():
        abort(404)
    form = EditPostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post_tags = PostTag.query.filter_by(post_id=post.id).all()
        for tag in post_tags:
            db.session.delete(tag)
        for tag in form.tags.data:
            post_tag = PostTag(post_id=post.id, tag_id=tag)
            db.session.add(post_tag)
        db.session.commit()
        flash("Post actualizado", category="success")
        return redirect(url_for("posts.get_post", id=post_id))
    form.title.data = post.title
    form.content.data = post.content
    form.tags.data = [tag.tag_id for tag in post.tags]
    return render_template("edit_post.html", form=form, post_id=post_id)


@posts_bp.route("/delete/<id>", methods=["GET", "POST"])
@login_required
def delete_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if current_user != post.author and not current_user.is_admin():
        abort(404)
    db.session.delete(post)
    db.session.commit()
    flash("Post eliminado", category="success")
    return redirect(url_for("posts.posts"))


@posts_bp.route("/show_all", methods=["GET", "POST"])
@login_required
def show_all():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("view_mode", "0", max_age=30 * 24 * 60 * 60)  # 30 days
    return resp


@posts_bp.route("/show_followed", methods=["GET", "POST"])
@login_required
def show_followed():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("view_mode", "1", max_age=30 * 24 * 60 * 60)  # 30 days
    return resp


@posts_bp.route("/show_favorite", methods=["GET", "POST"])
@login_required
def show_favorite():
    resp = make_response(redirect(url_for("posts.posts")))
    resp.set_cookie("view_mode", "2", max_age=30 * 24 * 60 * 60)  # 30 days
    return resp


@posts_bp.route("/moderate", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def moderate():
    return render_template("moderate.html")


@posts_bp.route("/moderate/comment", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment():
    page = request.args.get("page", 1, type=int)
    pagination = Comment.query.order_by(Comment.created_at.desc()).paginate(
        page, settings.POSTS_PER_PAGE, error_out=True
    )
    comments = pagination.items
    return render_template(
        "moderate_comment.html", comments=comments, pagination=pagination
    )


@posts_bp.route("/moderate/post", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def moderate_post():
    page = request.args.get("page", 1, type=int)
    pagination = (
        Post.query.join(Report, Report.post_id == Post.id)
        .order_by(Post.created_at.desc())
        .paginate(page, settings.POSTS_PER_PAGE, error_out=True)
    )
    posts = pagination.items
    return render_template("moderate_post.html", posts=posts, pagination=pagination)

@posts_bp.route("/moderate/post/enable_disable/<id>", methods=["GET"])
@login_required
def enable_disable_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.is_disabled():
        post.enable()
        return jsonify({"disable": False, "icon": "bi bi-star-fill"})
    else:
        post.disable()
        return jsonify({"disable": True, "icon": "bi bi-star"})

@posts_bp.route("/moderate/post/enable/<id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def post_enable(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.disabled = False
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    flash("Post habilitado", category="success")
    return redirect(url_for("posts.moderate_post", page=page))


@posts_bp.route("/moderate/post/disable/<id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.MODERATE)
def post_disable(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    post.disabled = True
    db.session.commit()
    page = request.args.get("page", 1, type=int)
    flash("Post deshabilitado", category="success")
    return redirect(url_for("posts.moderate_post", page=page))


@posts_bp.route("/moderate/comment/disable/<id>", methods=["GET"])
@login_required
@permission_required(Permission.MODERATE)
def moderate_comment_disable(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    if comment.disabled:
        comment.enable()
        return jsonify({"disable": False, "text": " Deshabilitar",  "content": comment.content})
    else:
        comment.disable()
        return jsonify({"disable": True, "text": " Habilitar"})

# @posts_bp.route("/moderate/comment/enable/<id>", methods=["GET", "POST"])
# @login_required
# @permission_required(Permission.MODERATE)
# def comment_enable(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.disabled = False
#     db.session.commit()
#     page = request.args.get("page", 1, type=int)
#     flash("Comentario habilitado", category="success")
#     return redirect(url_for("posts.moderate_comment", page=page))


# @posts_bp.route("/moderate/comment/disable/<id>", methods=["GET", "POST"])
# @login_required
# @permission_required(Permission.MODERATE)
# def comment_disable(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.disabled = True
#     db.session.commit()
#     page = request.args.get("page", 1, type=int)
#     flash("Comentario deshabilitado", category="success")
#     return redirect(url_for("posts.moderate_comment", page=page))


# @posts_bp.route("/like/<id>", methods=["GET", "POST"])
# @login_required
# def like_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.like(current_user)
#     # flash("Post agregado a likes", category="success")
#     return redirect(url_for("posts.get_post", id=id))

@posts_bp.route("/like_post/<id>", methods=["GET"])
@login_required
def like_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.is_like(current_user):
        post.unlike(current_user)
        return jsonify({"likes": post.likes.count(), "icon": "bi bi-star"})
    else:
        post.like(current_user)
        return jsonify({"likes": post.likes.count(), "icon": "bi bi-star-fill"})

# @posts_bp.route("/unlike/<id>", methods=["GET", "POST"])
# @login_required
# def unlike_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.unlike(current_user)
#     # flash("Post eliminado de likes", category="success")
#     return redirect(url_for("posts.get_post", id=id))


@posts_bp.route("/favorite_post/<id>", methods=["GET"])
@login_required
def favorite_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.is_favorite(current_user):
        post.unfavorite(current_user)
        return jsonify({"favorite": False, "icon": "bi bi-bookmark"})
    else:
        post.favorite(current_user)
        return jsonify({"favorite": True, "icon": "bi bi-bookmark-fill"})

# @posts_bp.route("/favorite/<id>", methods=["GET", "POST"])
# @login_required
# def favorite_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.favorite(current_user)
#     # flash("Post agregado a favoritos", category="success")
#     return redirect(url_for("posts.get_post", id=id))


# @posts_bp.route("/unfavorite/<id>", methods=["GET", "POST"])
# @login_required
# def unfavorite_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.unfavorite(current_user)
#     # flash("Post eliminado de favoritos", category="success")
#     return redirect(url_for("posts.get_post", id=id))


@posts_bp.route("/report_post/<id>", methods=["GET"])
@login_required
def report_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.is_report(current_user):
        post.delete_report(current_user)
        return jsonify({"report": False, "icon": "bi bi-flag"})
    else:
        post.add_report(current_user)
        return jsonify({"report": True, "icon": "bi bi-flag-fill"})


# @posts_bp.route("/report/<id>", methods=["GET", "POST"])
# @login_required
# def report_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.add_report(current_user)
#     # flash("Post agregado a reportes", category="success")
#     return redirect(url_for("posts.get_post", id=id))


# @posts_bp.route("/unreport/<id>", methods=["GET", "POST"])
# @login_required
# def unreport_post(id: int):
#     post = Post.query.filter_by(id=id).first_or_404()
#     post.delete_report(current_user)
#     # flash("Post eliminado de reportes", category="success")
#     return redirect(url_for("posts.get_post", id=id))


@posts_bp.route("/reply_comment/<id>", methods=["POST"])
@login_required
def reply_comment(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    if request.method == "POST":
        comment = Comment(
            content=request.form["comment"],
            author=current_user,
            parent_id=id,
            parent=comment,
            post=comment.post,
        )
        db.session.add(comment)
        db.session.commit()
        # flash("Comentario agregado", category="success")
        return redirect(url_for("posts.get_post", id=comment.post.id))
    return redirect(url_for("posts.get_post", id=comment.post.id))


@posts_bp.route("/post/close/<id>", methods=["GET", "POST"])
@login_required
def close_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.author == current_user or current_user.is_admin():
        post.close()
        # flash("Post cerrado", category="success")
        return redirect(url_for("posts.get_post", id=id))
    return redirect(url_for("posts.get_post", id=id))


@posts_bp.route("/post/open/<id>", methods=["GET", "POST"])
@login_required
def open_post(id: int):
    post = Post.query.filter_by(id=id).first_or_404()
    if post.author == current_user or current_user.is_admin():
        post.open()
        # flash("Post abierto", category="success")
        return redirect(url_for("posts.get_post", id=id))
    return redirect(url_for("posts.get_post", id=id))

@posts_bp.route("/report_comment/<id>", methods=["GET"])
@login_required
def report_comment(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    if comment.is_report(current_user):
        comment.delete_report(current_user)
        return jsonify({"reports": comment.reports.count(), "icon": "bi bi-flag"})
    else:
        comment.add_report(current_user)
        return jsonify({"reports": comment.reports.count(), "icon": "bi bi-flag-fill"})

# @posts_bp.route("/comment/report/<id>", methods=["GET", "POST"])
# @login_required
# def report_comment(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.add_report(current_user)
#     # flash("Comentario agregado a reportes", category="success")
#     return redirect(url_for("posts.get_post", id=comment.post.id))


# @posts_bp.route("/comment/unreport/<id>", methods=["GET", "POST"])
# @login_required
# def unreport_comment(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.delete_report(current_user)
#     # flash("Comentario eliminado de reportes", category="success")
#     return redirect(url_for("posts.get_post", id=comment.post.id))



@posts_bp.route("/like_comment/<id>", methods=["GET"])
@login_required
def like_comment(id: int):
    comment = Comment.query.filter_by(id=id).first_or_404()
    if comment.is_like(current_user):
        comment.unlike(current_user)
        return jsonify({"likes": comment.likes.count(), "icon": "bi bi-star"})
    else:
        comment.like(current_user)
        return jsonify({"likes": comment.likes.count(), "icon": "bi bi-star-fill"})

# @posts_bp.route("/comment/like/<id>", methods=["GET", "POST"])
# @login_required
# def like_comment(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.like(current_user)
#     # flash("Comentario agregado a likes", category="success")
#     return redirect(url_for("posts.get_post", id=comment.post.id))


# @posts_bp.route("/comment/unlike/<id>", methods=["GET", "POST"])
# @login_required
# def unlike_comment(id: int):
#     comment = Comment.query.filter_by(id=id).first_or_404()
#     comment.unlike(current_user)
#     # flash("Comentario eliminado de likes", category="success")
#     return redirect(url_for("posts.get_post", id=comment.post.id))
