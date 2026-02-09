from flask import Blueprint, render_template, request
from flask_login import login_required

from app.services.password_generator import PasswordGenerator

generator_bp = Blueprint("generator", __name__, url_prefix="/generator")


@generator_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    password = None
    strength = None

    if request.method == "POST":
        length = request.form.get("length", 20, type=int)
        length = max(8, min(128, length))

        password = PasswordGenerator.generate(
            length=length,
            use_uppercase=bool(request.form.get("uppercase", True)),
            use_lowercase=bool(request.form.get("lowercase", True)),
            use_digits=bool(request.form.get("digits", True)),
            use_symbols=bool(request.form.get("symbols", True)),
            exclude_ambiguous=bool(request.form.get("exclude_ambiguous", True)),
        )
        strength = PasswordGenerator.calculate_strength(password)

    return render_template(
        "generator/index.html",
        password=password,
        strength=strength,
    )
