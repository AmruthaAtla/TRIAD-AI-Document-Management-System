import sys
import json
from pathlib import Path
from io import BytesIO

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, extensions
from flask_jwt_extended import create_access_token
from bson import ObjectId

app = create_app()
client = app.test_client()
db = extensions.db

def test_normal_user_upload():
    print("=== Testing Normal User Document Upload ===")

    # Setup normal user
    db.users.delete_many({"email": "normal_uploader@test.com"})
    user_id = db.users.insert_one({
        "name": "Normal Uploader",
        "email": "normal_uploader@test.com",
        "password": "hashed_password",
        "division": "Engineering",
        "role": "user"
    }).inserted_id

    with app.app_context():
        token = create_access_token(
            identity=str(user_id),
            additional_claims={"role": "user", "division": "Engineering"}
        )

    headers = {"Authorization": f"Bearer {token}"}

    # 1. Fetch metadata as normal user (Task 1 verification)
    meta_res = client.get("/api/admin/metadata", headers=headers)
    assert meta_res.status_code == 200, f"Expected 200, got {meta_res.status_code}"
    fields = meta_res.get_json()["metadata_fields"]
    print(f"[PASS] Successfully fetched {len(fields)} metadata fields as normal user")

    # 2. Upload document with valid metadata (including number as int)
    sample_pdf = ROOT_DIR / "test_sample.pdf"
    with open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()

    metadata = {
        "Department": "Engineering",
        "Project Name": "Normal User Test Project",
        "Financial Year": 2026,
        "Report Date": "2026-11-17"
    }

    upload_data = {
        "title": "Normal User Uploaded Doc",
        "metadata": json.dumps(metadata),
        "file": (BytesIO(pdf_bytes), "normal_user_sample.pdf")
    }

    res = client.post(
        "/api/documents/upload",
        headers=headers,
        data=upload_data,
        content_type="multipart/form-data"
    )

    assert res.status_code == 201, f"Expected 201, got {res.status_code}: {res.get_json()}"
    doc_id = res.get_json()["document_id"]
    print(f"[PASS] Normal user uploaded document successfully. Doc ID: {doc_id}")

    # 3. Verify document exists in DB and division matches
    doc = db.documents.find_one({"_id": ObjectId(doc_id)})
    assert doc is not None
    assert doc["division"] == "Engineering"
    assert doc["metadata"]["Financial Year"] == 2026
    print("[PASS] Verified document persisted in MongoDB with correct division and metadata")

    # 4. Clean up
    client.delete(f"/api/documents/{doc_id}", headers=headers)
    db.users.delete_one({"_id": user_id})
    print("\nNORMAL USER UPLOAD TEST COMPLETED SUCCESSFULLY!")

if __name__ == "__main__":
    test_normal_user_upload()
