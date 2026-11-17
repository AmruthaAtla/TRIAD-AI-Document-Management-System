
from flask import Blueprint, request, jsonify
from bson import ObjectId
from datetime import datetime, timezone

from app.extensions import db
from app.middleware.auth_middleware import token_required

access_bp = Blueprint(
    "access",
    __name__,
    url_prefix="/api/access"
)


# 1. Request access to another division's document
@access_bp.route("/request", methods=["POST"])
@token_required
def request_access(user):

    data = request.get_json() or {}

    document_id = data.get("document_id")
    reason = data.get("reason", "").strip()

    if not document_id:
        return jsonify({
            "error": "Document ID is required"
        }), 400

    try:
        document = db.documents.find_one({
            "_id": ObjectId(document_id)
        })

    except Exception:
        return jsonify({
            "error": "Invalid document ID"
        }), 400

    if not document:
        return jsonify({
            "error": "Document not found"
        }), 404

    if document["division"] == user["division"]:
        return jsonify({
            "error": "You already have access to this division's document"
        }), 400

    existing_request = db.access_requests.find_one({
        "document_id": ObjectId(document_id),
        "requested_by": ObjectId(user["_id"]),
        "status": "pending"
    })

    if existing_request:
        return jsonify({
            "error": "An access request is already pending"
        }), 409

    access_request = {
        "document_id": ObjectId(document_id),
        "document_title": document.get(
            "title",
            document.get("filename")
        ),
        "requested_by": ObjectId(user["_id"]),
        "requester_name": user["name"],
        "requester_division": user["division"],
        "document_division": document["division"],
        "reason": reason,
        "status": "pending",
        "requested_at": datetime.now(timezone.utc),
        "reviewed_at": None,
        "reviewed_by": None
    }

    result = db.access_requests.insert_one(access_request)

    return jsonify({
        "message": "Access request submitted successfully",
        "request_id": str(result.inserted_id),
        "status": "pending"
    }), 201


# 2. View access requests (incoming for user's division, or outgoing submitted by user)
@access_bp.route("/requests", methods=["GET"])
@token_required
def get_access_requests(user):

    req_type = request.args.get("type", "incoming").strip().lower()

    if req_type == "outgoing":
        # Outgoing requests submitted by the logged-in user
        requests_list = list(db.access_requests.find({
            "requested_by": ObjectId(user["_id"])
        }).sort("requested_at", -1))
    else:
        # Incoming pending requests for documents in the user's division
        requests_list = list(db.access_requests.find({
            "document_division": user["division"],
            "status": "pending"
        }).sort("requested_at", -1))

    results = []

    for item in requests_list:

        results.append({
            "request_id": str(item["_id"]),
            "document_id": str(item["document_id"]),
            "document_title": item.get("document_title", ""),
            "requested_by": str(item["requested_by"]),
            "requester_name": item.get("requester_name", ""),
            "requester_division": item.get("requester_division", ""),
            "document_division": item.get("document_division", ""),
            "reason": item.get("reason", ""),
            "status": item["status"],
            "requested_at": item["requested_at"].isoformat() if item.get("requested_at") else "",
            "reviewed_at": item["reviewed_at"].isoformat() if item.get("reviewed_at") else None
        })

    return jsonify({
        "requests": results,
        "total": len(results)
    }), 200


# 3. Approve or reject an access request
@access_bp.route("/approve", methods=["POST"])
@token_required
def review_access_request(user):

    data = request.get_json() or {}

    request_id = data.get("request_id")
    decision = data.get("decision")

    if not request_id or decision not in ["approved", "rejected"]:
        return jsonify({
            "error": "Valid request_id and decision are required"
        }), 400

    try:
        access_request = db.access_requests.find_one({
            "_id": ObjectId(request_id)
        })

    except Exception:
        return jsonify({
            "error": "Invalid request ID"
        }), 400

    if not access_request:
        return jsonify({
            "error": "Access request not found"
        }), 404

    if access_request["document_division"] != user["division"]:
        return jsonify({
            "error": "You are not authorized to review this request"
        }), 403

    if access_request["status"] != "pending":
        return jsonify({
            "error": "This request has already been reviewed"
        }), 409

    result = db.access_requests.update_one(
        {
            "_id": ObjectId(request_id),
            "status": "pending"
        },
        {
            "$set": {
                "status": decision,
                "reviewed_by": ObjectId(user["_id"]),
                "reviewed_at": datetime.now(timezone.utc)
            }
        }
    )

    # Check whether the request was successfully updated
    if result.modified_count == 0:
        return jsonify({
            "error": "Request could not be updated"
        }), 409

    # Return approval/rejection confirmation
    return jsonify({
        "message": f"Access request {decision} successfully",
        "status": decision
    }), 200
