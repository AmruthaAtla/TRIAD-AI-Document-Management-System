from datetime import datetime, timezone
from bson import ObjectId

from app.extensions import db


class Document:

    @staticmethod
    def create_document(
        title,
        filename,
        file_id,
        uploaded_by,
        division,
        metadata=None,
        description=""
    ):
        document = {
            "title": title,
            "filename": filename,
            "description": description or "",
            "file_id": file_id,
            "uploaded_by": ObjectId(uploaded_by),
            "division": division,
            "metadata": metadata or {},
            "ocr_text": "",
            "uploaded_at": datetime.now(timezone.utc)
        }

        result = db.documents.insert_one(document)

        return str(result.inserted_id)

    @staticmethod
    def find_by_id(document_id):
        if not ObjectId.is_valid(document_id):
            return None

        return db.documents.find_one({
            "_id": ObjectId(document_id)
        })

    @staticmethod
    def find_by_division(division):
        return list(
            db.documents.find({
                "division": division
            }).sort("uploaded_at", -1)
        )

    @staticmethod
    def update_ocr_text(document_id, extracted_text):
        if not ObjectId.is_valid(document_id):
            return False

        result = db.documents.update_one(
            {"_id": ObjectId(document_id)},
            {"$set": {"ocr_text": extracted_text}}
        )

        return result.modified_count > 0

    @staticmethod
    def serialize(document):
         return {
            "id": str(document["_id"]),
            "title": document["title"],
            "filename": document["filename"],
            "description": document.get("description", ""),
            "uploaded_by": str(document["uploaded_by"]),
            "division": document["division"],
            "metadata": document.get("metadata", {}),
            "ocr_text": document.get("ocr_text", ""),
            "uploaded_at": document["uploaded_at"].isoformat()
        }

    @staticmethod
    def delete_by_id(document_id):
        if not ObjectId.is_valid(document_id):
            return False

        result = db.documents.delete_one({
            "_id": ObjectId(document_id)
        })

        return result.deleted_count > 0