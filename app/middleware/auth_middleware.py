from functools import wraps
from flask import jsonify, current_app
from flask_jwt_extended import verify_jwt_in_request, get_jwt, get_jwt_identity
from bson import ObjectId

from app.extensions import db


def token_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()

            user_id = get_jwt_identity()

            user = db.users.find_one({
                "_id": ObjectId(user_id)
            })

            if not user:
                return jsonify({
                    "error": "User not found"
                }), 404

            return fn(user, *args, **kwargs)

        except Exception:
            return jsonify({
                "error": "Authentication required or token invalid"
            }), 401

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            verify_jwt_in_request()

            claims = get_jwt()

            if claims.get("role") != "admin":
                return jsonify({
                    "error": "Admin access required"
                }), 403

            user_id = get_jwt_identity()

            user = db.users.find_one({
                "_id": ObjectId(user_id)
            })

            if not user:
                return jsonify({
                    "error": "User not found"
                }), 404

            return fn(user, *args, **kwargs)

        except Exception:
            current_app.logger.exception("Authentication middleware failed")
            return jsonify({
                "error": "Authentication failed. Check backend terminal."
            }), 401

    return wrapper