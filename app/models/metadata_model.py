"""
Metadata configuration model helpers and schema definition.
"""
from datetime import datetime, timezone
from bson import ObjectId
from app.extensions import db


class MetadataField:
    @staticmethod
    def get_all_fields():
        return list(db.metadata_fields.find())

    @staticmethod
    def find_by_name(field_name):
        return db.metadata_fields.find_one({"field_name": field_name})

    @staticmethod
    def create_field(field_name, field_type, required=False, options=None, created_by=None):
        doc = {
            "field_name": field_name,
            "field_type": field_type,
            "required": bool(required),
            "options": options or [],
            "created_by": str(created_by) if created_by else None,
            "created_at": datetime.now(timezone.utc)
        }
        result = db.metadata_fields.insert_one(doc)
        return str(result.inserted_id)
