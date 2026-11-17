"""
Service layer for cross-division access management.
"""
from bson import ObjectId
from datetime import datetime, timezone
from app.extensions import db


def check_document_access(user, document):
    """
    Check whether a user has access to a document.
    Access is granted if same division or approved via access_requests.
    """
    if document.get("division") == user.get("division"):
        return True

    approved = db.access_requests.find_one({
        "document_id": document["_id"],
        "requested_by": user["_id"],
        "status": "approved"
    })
    return approved is not None
