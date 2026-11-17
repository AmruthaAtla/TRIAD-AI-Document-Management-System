from flask import Blueprint, request, jsonify
from bson import ObjectId

from app.extensions import db
from app.middleware.auth_middleware import token_required
from app.models.document_model import Document


search_bp = Blueprint(
    "search",
    __name__,
    url_prefix="/api"
)


def search_metadata(metadata, query):
    """
    Recursively search metadata values.
    Supports text, numbers, lists and nested dictionaries.
    """

    if isinstance(metadata, dict):
        return any(
            search_metadata(value, query)
            for value in metadata.values()
        )

    elif isinstance(metadata, list):
        return any(
            search_metadata(value, query)
            for value in metadata
        )

    elif metadata is not None:
        return query in str(metadata).lower()

    return False


@search_bp.route("/search", methods=["GET"])
@token_required
def search_documents(user):

    query = request.args.get("q", "").strip().lower()

    if not query:
        return jsonify({
            "error": "Search query is required"
        }), 400

    # Retrieve approved cross-division document IDs for this user
    approved_requests = list(db.access_requests.find({
        "requested_by": ObjectId(user["_id"]),
        "status": "approved"
    }, {"document_id": 1}))
    approved_ids = {str(req["document_id"]) for req in approved_requests}

    # Retrieve all documents for search and secure discovery
    documents = list(
        db.documents.find().sort("uploaded_at", -1)
    )

    results = []

    for document in documents:
        doc_id = str(document["_id"])
        doc_division = document.get("division", "")
        has_access = (doc_division == user["division"]) or (doc_id in approved_ids)

        title = document.get("title", "").lower()
        filename = document.get("filename", "").lower()

        title_match = query in title
        filename_match = query in filename

        if has_access:
            # Full-content search (including custom metadata and OCR content)
            ocr_text = document.get("ocr_text", "").lower()
            metadata = document.get("metadata", {})

            ocr_match = query in ocr_text
            metadata_match = search_metadata(metadata, query)

            if (
                title_match
                or filename_match
                or ocr_match
                or metadata_match
            ):
                result = Document.serialize(document)
                result["has_access"] = True
                result["matched_in"] = []

                if title_match:
                    result["matched_in"].append("title")
                if filename_match:
                    result["matched_in"].append("filename")
                if metadata_match:
                    result["matched_in"].append("metadata")
                if ocr_match:
                    result["matched_in"].append("ocr_text")

                results.append(result)

        else:
            # Secure Cross-Division Discovery:
            # Only match public headers (title / filename); NEVER inspect or expose OCR text or sensitive metadata
            if title_match or filename_match:
                result = {
                    "id": doc_id,
                    "title": document.get("title", ""),
                    "filename": document.get("filename", ""),
                    "division": doc_division,
                    "uploaded_at": document["uploaded_at"].isoformat() if hasattr(document.get("uploaded_at"), "isoformat") else str(document.get("uploaded_at")),
                    "has_access": False,
                    "matched_in": []
                }
                if title_match:
                    result["matched_in"].append("title")
                if filename_match:
                    result["matched_in"].append("filename")

                results.append(result)

    return jsonify({
        "query": query,
        "total": len(results),
        "results": results
    }), 200