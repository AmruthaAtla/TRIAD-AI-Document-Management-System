from app.middleware.auth_middleware import token_required
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from pymongo.errors import DuplicateKeyError

from app.models.user_model import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    division = data.get("division", "").strip()

    if not all([name, email, password, division]):
        return jsonify({
            "error": "Name, email, password and division are required"
        }), 400

    if len(password) < 8:
        return jsonify({
            "error": "Password must contain at least 8 characters"
        }), 400

    if "@" not in email:
        return jsonify({"error": "Invalid email address"}), 400

    try:
        # Ensure email addresses are unique
        db.users.create_index("email", unique=True)

        user_id = User.create_user(
            name=name,
            email=email,
            password=password,
            division=division
        )

        return jsonify({
            "message": "User registered successfully",
            "user_id": user_id
        }), 201

    except DuplicateKeyError:
        return jsonify({"error": "Email already registered"}), 409


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"error": "JSON data is required"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({
            "error": "Email and password are required"
        }), 400

    user = User.find_by_email(email)

    if not user or not User.verify_password(user, password):
        return jsonify({
            "error": "Invalid email or password"
        }), 401

    access_token = create_access_token(
        identity=str(user["_id"]),
        additional_claims={
            "role": user["role"],
            "division": user["division"]
        }
    )

    return jsonify({
        "message": "Login successful",
        "access_token": access_token,
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "division": user["division"],
            "role": user["role"]
        }
    }), 200


@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(user):
    return jsonify({
        "message": "Authenticated user details",
        "user": {
            "id": str(user["_id"]),
            "name": user["name"],
            "email": user["email"],
            "division": user["division"],
            "role": user["role"]
        }
    }), 200