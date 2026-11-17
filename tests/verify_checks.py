import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, extensions
from bson import ObjectId

app = create_app()
client = app.test_client()
db = extensions.db

def test_checks():
    print("=== RUNNING RIGOROUS CHECKS 1, 2, 3 ===")

    # Setup test users
    db.users.delete_many({"email": {"$in": ["u_div_a@t.com", "u_div_b1@t.com", "u_div_b2@t.com", "u_div_c@t.com"]}})

    # Division A User
    res = client.post("/api/auth/register", json={"name": "User A", "email": "u_div_a@t.com", "password": "Password123!", "division": "Division A"})
    uid_a = res.get_json()["user_id"]
    token_a = client.post("/api/auth/login", json={"email": "u_div_a@t.com", "password": "Password123!"}).get_json()["access_token"]
    h_a = {"Authorization": f"Bearer {token_a}"}

    # Division B User 1 (Requester)
    res = client.post("/api/auth/register", json={"name": "User B1", "email": "u_div_b1@t.com", "password": "Password123!", "division": "Division B"})
    uid_b1 = res.get_json()["user_id"]
    token_b1 = client.post("/api/auth/login", json={"email": "u_div_b1@t.com", "password": "Password123!"}).get_json()["access_token"]
    h_b1 = {"Authorization": f"Bearer {token_b1}"}

    # Division B User 2 (Colleague in Division B)
    res = client.post("/api/auth/register", json={"name": "User B2", "email": "u_div_b2@t.com", "password": "Password123!", "division": "Division B"})
    uid_b2 = res.get_json()["user_id"]
    token_b2 = client.post("/api/auth/login", json={"email": "u_div_b2@t.com", "password": "Password123!"}).get_json()["access_token"]
    h_b2 = {"Authorization": f"Bearer {token_b2}"}

    # Division C User (Unauthorized division)
    res = client.post("/api/auth/register", json={"name": "User C", "email": "u_div_c@t.com", "password": "Password123!", "division": "Division C"})
    uid_c = res.get_json()["user_id"]
    token_c = client.post("/api/auth/login", json={"email": "u_div_c@t.com", "password": "Password123!"}).get_json()["access_token"]
    h_c = {"Authorization": f"Bearer {token_c}"}

    # User A uploads a document
    sample_pdf = ROOT_DIR / "test_sample.pdf"
    with open(sample_pdf, "rb") as f:
        pdf_bytes = f.read()

    from io import BytesIO
    import json

    upload_res = client.post("/api/documents/upload", headers=h_a, data={
        "title": "Division A Financial Projections",
        "description": "TOP SECRET financial projection details.",
        "metadata": json.dumps({"Department": "Finance", "Project Name": "SecretProj", "Financial Year": 2026}),
        "file": (BytesIO(pdf_bytes), "financial_projections.pdf")
    }, content_type="multipart/form-data")

    assert upload_res.status_code == 201
    doc_id = upload_res.get_json()["document_id"]
    print(f"Uploaded Doc ID: {doc_id}")

    # -------------------------------------------------------------
    # CHECK 1: Inspect actual search response for cross-division User B1
    # -------------------------------------------------------------
    search_res = client.get("/api/search?q=Projections", headers=h_b1)
    assert search_res.status_code == 200
    search_data = search_res.get_json()
    assert search_data["total"] >= 1
    found_item = [x for x in search_data["results"] if x["id"] == doc_id][0]

    print("\n--- CHECK 1: ACTUAL SEARCH RESPONSE PAYLOAD (CROSS-DIVISION) ---")
    print(json.dumps(found_item, indent=2))
    print("------------------------------------------------------------------\n")

    # Validate Check 1 guarantees
    assert "description" not in found_item, "VIOLATION: description exposed!"
    assert "uploaded_by" not in found_item, "VIOLATION: uploaded_by exposed!"
    assert "ocr_text" not in found_item, "VIOLATION: ocr_text exposed!"
    assert "metadata" not in found_item, "VIOLATION: metadata exposed!"
    assert "file_id" not in found_item, "VIOLATION: file_id exposed!"
    assert found_item.get("has_access") is False, "VIOLATION: has_access is not False!"
    print("[PASS] CHECK 1: Only document header exposed. Description, uploaded_by, OCR text, metadata, and file_id are NOT exposed.")

    # -------------------------------------------------------------
    # CHECK 2: User from another division CANNOT approve access requests
    # -------------------------------------------------------------
    # User B1 requests access to Doc A
    req_res = client.post("/api/access/request", headers=h_b1, json={
        "document_id": doc_id,
        "reason": "Need budget alignment"
    })
    assert req_res.status_code == 201
    req_id = req_res.get_json()["request_id"]

    # User C (Division C) attempts to approve request for Division A document -> Must be 403
    unauth_approve = client.post("/api/access/approve", headers=h_c, json={
        "request_id": req_id,
        "decision": "approved"
    })
    print(f"Division C approval attempt status: {unauth_approve.status_code}, response: {unauth_approve.get_json()}")
    assert unauth_approve.status_code == 403, f"VIOLATION: Expected 403, got {unauth_approve.status_code}"
    assert "not authorized" in unauth_approve.get_json().get("error", "").lower()

    # User B1 (requester) also cannot approve their own request
    self_approve = client.post("/api/access/approve", headers=h_b1, json={
        "request_id": req_id,
        "decision": "approved"
    })
    assert self_approve.status_code == 403
    print("[PASS] CHECK 2: Users cannot approve access requests belonging to another division (HTTP 403).")

    # -------------------------------------------------------------
    # CHECK 3: Approved access is ONLY for the requesting user (User B1), NOT other division users (User B2)
    # -------------------------------------------------------------
    # User A (Division A) approves the request
    auth_approve = client.post("/api/access/approve", headers=h_a, json={
        "request_id": req_id,
        "decision": "approved"
    })
    assert auth_approve.status_code == 200

    # User B1 (the requester) MUST have access now
    b1_details = client.get(f"/api/documents/{doc_id}", headers=h_b1)
    assert b1_details.status_code == 200, f"Expected 200 for requester B1, got {b1_details.status_code}"
    b1_dl = client.get(f"/api/documents/{doc_id}/download", headers=h_b1)
    assert b1_dl.status_code == 200, f"Expected 200 for download by requester B1, got {b1_dl.status_code}"
    b1_list = client.get("/api/documents", headers=h_b1).get_json()["documents"]
    assert any(d["id"] == doc_id for d in b1_list), "Doc A should be in requester B1's document list"

    # User B2 (colleague in Division B, NOT the requester) MUST STILL BE FORBIDDEN
    b2_details = client.get(f"/api/documents/{doc_id}", headers=h_b2)
    assert b2_details.status_code == 403, f"VIOLATION: User B2 accessed details! Status: {b2_details.status_code}"
    b2_dl = client.get(f"/api/documents/{doc_id}/download", headers=h_b2)
    assert b2_dl.status_code == 403, f"VIOLATION: User B2 downloaded document! Status: {b2_dl.status_code}"
    b2_list = client.get("/api/documents", headers=h_b2).get_json()["documents"]
    assert not any(d["id"] == doc_id for d in b2_list), "VIOLATION: Doc A appeared in User B2's document list!"

    print("[PASS] CHECK 3: Approved documents become accessible ONLY to the requesting user (User B1). Other users in that division (User B2) do NOT receive access.")

    # Cleanup
    client.delete(f"/api/documents/{doc_id}", headers=h_a)
    db.users.delete_many({"_id": {"$in": [ObjectId(uid_a), ObjectId(uid_b1), ObjectId(uid_b2), ObjectId(uid_c)]}}
    )
    db.access_requests.delete_many({"document_id": ObjectId(doc_id)})
    print("\nALL PRE-ACCEPTANCE VERIFICATION CHECKS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_checks()
