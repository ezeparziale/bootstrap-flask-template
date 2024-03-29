from flask import Blueprint, render_template
from flask_login import login_required

from app.decorators import admin_required, password_not_expired

admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin",
    template_folder="templates",
    static_folder="static",
)


@admin_bp.before_request
@password_not_expired
def before_request():
    pass


# Blueprint nested
from .tags import tags_bp  # type: ignore  # noqa

admin_bp.register_blueprint(tags_bp)


from .users import users_bp  # type: ignore  # noqa

admin_bp.register_blueprint(users_bp)


@admin_bp.route("/", methods=["GET"])
@login_required
@admin_required
def admin_view():
    return render_template("admin/admin.html")
