"""
Service layer for dynamic metadata retrieval and validation.
"""
from app.extensions import db


def get_configured_fields():
    """Retrieve all configured metadata field definitions."""
    return list(db.metadata_fields.find())
