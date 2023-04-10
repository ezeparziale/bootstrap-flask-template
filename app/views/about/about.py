from flask import Blueprint, render_template

from app.decorators import password_not_expired

about_bp = Blueprint("about", __name__, template_folder="templates")


@about_bp.route("/about")
@password_not_expired
def about_view():
    return render_template("about/about.html")
