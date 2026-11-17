from flask import Blueprint, request, jsonify
from datetime import datetime, timezone

from app.extensions import db
from app.middleware.auth_middleware import admin_required, token_required


admin_bp = Blueprint(
    "admin",
    __name__,
    url_prefix="/api/admin"
)


# Add a new metadata field configuration
@admin_bp.route("/metadata", methods=["POST"])
@admin_required
def create_metadata_field(user):

    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required"}), 400

    field_name = data.get("field_name", "").strip()
    field_type = data.get("field_type", "").lower()
    required = data.get("required", False)
    options = data.get("options", [])

    if not field_name:
        return jsonify({"error": "Field name is required"}), 400

    if field_type not in ["text", "number", "date", "dropdown"]:
        return jsonify({"error": "Invalid field type"}), 400

    if not isinstance(required, bool):
        return jsonify({"error": "Required must be true or false"}), 400

    if field_type == "dropdown":
        if not isinstance(options, list) or not options:
            return jsonify({
                "error": "Dropdown fields require options"
            }), 400

    else:
        options = []

    existing_field = db.metadata_fields.find_one({
        "field_name": field_name
    })

    if existing_field:
        return jsonify({
            "error": "Metadata field already exists"
        }), 409

    metadata_field = {
        "field_name": field_name,
        "field_type": field_type,
        "required": required,
        "options": options,
        "created_by": str(user["_id"]),
        "created_at": datetime.now(timezone.utc)
    }

    result = db.metadata_fields.insert_one(metadata_field)

    return jsonify({
        "message": "Metadata field created successfully",
        "field_id": str(result.inserted_id),
        "field_name": field_name
    }), 201


# Retrieve all configured metadata fields
@admin_bp.route("/metadata", methods=["GET"])
@token_required
def get_metadata_fields(user):

    fields = list(db.metadata_fields.find())

    result = []

    for field in fields:
        result.append({
            "field_id": str(field["_id"]),
            "field_name": field["field_name"],
            "field_type": field["field_type"],
            "required": field["required"],
            "options": field["options"]
        })

    return jsonify({
        "total": len(result),
        "metadata_fields": result
    }), 200