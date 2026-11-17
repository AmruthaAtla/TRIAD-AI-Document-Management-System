"""
Access request model helpers and schema definition.
"""
from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import db


class AccessRequest:
    @staticmethod
    def create_request(document_id, document_title, requested_by, requester_name, requester_division, document_division, reason=""):
        request_doc = {
            "document_id": ObjectId(document_id),
            "document_title": document_title,
            "requested_by": ObjectId(requested_by),
            "requester_name": requester_name,
            "requester_division": requester_division,
            "document_division": document_division,
            "reason": reason,
            "status": "pending",
            "requested_at": datetime.now(timezone.utc),
            "reviewed_at": None,
            "reviewed_by": None
        }
        result = db.access_requests.insert_one(request_doc)
        return str(result.inserted_id)

    @staticmethod
    def find_by_id(request_id):
        if not ObjectId.is_valid(request_id):
            return None
        return db.access_requests.find_one({"_id": ObjectId(request_id)})
