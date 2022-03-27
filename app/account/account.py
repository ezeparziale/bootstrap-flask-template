from flask import Blueprint, redirect, render_template
from flask_login import login_required

account_bp = Blueprint("account", __name__, url_prefix="/account", template_folder='templates')

@account_bp.route("/", methods=["GET", "POST"])
@login_required
def account():
    return render_template("account.html")