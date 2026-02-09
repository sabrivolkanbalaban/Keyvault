from flask import jsonify, request
from flask_login import login_required

from app.api.v1 import api_v1_bp
from app.services.password_generator import PasswordGenerator


@api_v1_bp.route("/generator/password", methods=["POST"])
@login_required
def api_generate_password():
    data = request.get_json() or {}

    length = data.get("length", 20)
    length = max(8, min(128, length))

    password = PasswordGenerator.generate(
        length=length,
        use_uppercase=data.get("uppercase", True),
        use_lowercase=data.get("lowercase", True),
        use_digits=data.get("digits", True),
        use_symbols=data.get("symbols", True),
        exclude_ambiguous=data.get("exclude_ambiguous", True),
    )
    strength = PasswordGenerator.calculate_strength(password)

    return jsonify({
        "success": True,
        "data": {
            "password": password,
            "strength": strength,
        },
    })
