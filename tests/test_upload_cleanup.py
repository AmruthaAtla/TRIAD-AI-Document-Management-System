import sys
import json
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from io import BytesIO
from unittest.mock import patch

from app import create_app

# Initialize Flask and MongoDB first
app = create_app()

# Import database only after initialization
from app import extensions

db = extensions.db

client = app.test_client()


EMAIL = "testa20261116000728@example.com"
PASSWORD = "TestPass123"

filename = "cleanup_test.pdf"
title = "Cleanup Failure Test"

# Login
login = client.post(
    "/api/auth/login",
    json={"email": EMAIL, "password": PASSWORD}
)

assert login.status_code == 200, "Login failed"

token = login.get_json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

metadata = {
    "Department": "Finance",
    "Project Name": "Cleanup Test",
    "Financial Year": 2026,
    "Report Date": "2026-11-16"
}

print("\n=== UPLOAD CLEANUP TEST ===")

# Simulate failure after GridFS upload and MongoDB document creation
with patch(
    "app.routes.document_routes.download_file",
    side_effect=RuntimeError("Simulated failure")
):
    response = client.post(
        "/api/documents/upload",
        headers=headers,
        data={
            "title": title,
            "metadata": __import__("json").dumps(metadata),
            "file": (
                BytesIO(b"%PDF-1.4\nTest PDF content\n%%EOF"),
                filename
            )
        },
        content_type="multipart/form-data"
    )

print("Upload response:", response.status_code)
print("Response body:", response.get_json())

# Check whether MongoDB document record remains
document = db.documents.find_one({
    "title": title
})

# Check whether GridFS file remains
gridfs_file = db.fs.files.find_one({
    "filename": filename
})

print(
    "MongoDB document cleanup:",
    "PASS" if document is None else "FAIL"
)

print(
    "GridFS file cleanup:",
    "PASS" if gridfs_file is None else "FAIL"
)

assert response.status_code == 500
assert document is None
assert gridfs_file is None

print("\nALL CLEANUP CHECKS PASSED")