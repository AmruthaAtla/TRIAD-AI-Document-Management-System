import subprocess
import time
import sys
import json
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
python_exe = sys.executable

print("Starting Flask server for live verification...")
server_process = subprocess.Popen(
    [python_exe, "run.py"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

# Wait for server to be responsive
url = "http://127.0.0.1:5000/api/health/db"
started = False
for _ in range(30):
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            started = True
            print("Flask server is up and responsive on http://127.0.0.1:5000!")
            break
    except Exception:
        time.sleep(1)

if not started:
    print("Failed to start Flask server in time.")
    server_process.terminate()
    sys.exit(1)

BASE_URL = "http://127.0.0.1:5000/api"

try:
    print("\n--- RUNNING CHECK 1, 2, 3 VERIFICATION VIA LIVE API ---")
    import uuid
    suffix = uuid.uuid4().hex[:6]

    # Register Division A user
    email_a = f"alice_{suffix}@diva.com"
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Alice Diva", "email": email_a, "password": "Password123!", "division": "Division A"
    })
    token_a = requests.post(f"{BASE_URL}/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    h_a = {"Authorization": f"Bearer {token_a}"}

    # Register Division B user 1 (requester)
    email_b1 = f"bob1_{suffix}@divb.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Bob B1", "email": email_b1, "password": "Password123!", "division": "Division B"
    })
    token_b1 = requests.post(f"{BASE_URL}/auth/login", json={"email": email_b1, "password": "Password123!"}).json()["access_token"]
    h_b1 = {"Authorization": f"Bearer {token_b1}"}

    # Register Division B user 2 (colleague)
    email_b2 = f"bob2_{suffix}@divb.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Bob B2", "email": email_b2, "password": "Password123!", "division": "Division B"
    })
    token_b2 = requests.post(f"{BASE_URL}/auth/login", json={"email": email_b2, "password": "Password123!"}).json()["access_token"]
    h_b2 = {"Authorization": f"Bearer {token_b2}"}

    # Register Division C user
    email_c = f"charlie_{suffix}@divc.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Charlie C", "email": email_c, "password": "Password123!", "division": "Division C"
    })
    token_c = requests.post(f"{BASE_URL}/auth/login", json={"email": email_c, "password": "Password123!"}).json()["access_token"]
    h_c = {"Authorization": f"Bearer {token_c}"}

    # Alice uploads document to Division A
    with open(ROOT_DIR / "test_sample.pdf", "rb") as f:
        pdf_bytes = f.read()

    upload_res = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=h_a,
        data={
            "title": f"Confidential Strategy {suffix}",
            "description": "Sensitive strategic plan for Division A.",
            "metadata": json.dumps({"Division": "Division A", "Report Type": "Financial"})
        },
        files={"file": ("strategy.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    doc_id = upload_res.json()["document_id"]
    print(f"Uploaded test document {doc_id} by Alice (Division A)")

    # =========================================================================
    # CHECK 1: Search response for unauthorized cross-division user (Bob B1)
    # =========================================================================
    search_res = requests.get(f"{BASE_URL}/search?q=Confidential", headers=h_b1)
    assert search_res.status_code == 200
    search_json = search_res.json()
    matches = [d for d in search_json["results"] if d["id"] == doc_id]
    assert len(matches) == 1
    found_item = matches[0]

    print("\n--- ACTUAL RAW SEARCH RESPONSE PAYLOAD (CROSS-DIVISION UNAUTHORIZED) ---")
    print(json.dumps(found_item, indent=2))
    print("------------------------------------------------------------------------\n")

    # Assertions for Check 1:
    assert "description" not in found_item, "FAILED: 'description' is exposed!"
    assert "uploaded_by" not in found_item, "FAILED: 'uploaded_by' is exposed!"
    assert "ocr_text" not in found_item, "FAILED: 'ocr_text' is exposed!"
    assert "metadata" not in found_item, "FAILED: 'metadata' is exposed!"
    assert "file_id" not in found_item, "FAILED: 'file_id' is exposed!"
    assert found_item.get("has_access") is False, "FAILED: 'has_access' should be False!"
    assert set(found_item.keys()) == {"id", "title", "filename", "division", "uploaded_at", "has_access", "matched_in"}, f"Unexpected keys: {list(found_item.keys())}"
    print("[PASS] CHECK 1: Only document header exposed. Description, uploaded_by, OCR text, metadata, and GridFS file IDs are strictly NOT exposed.")

    # =========================================================================
    # CHECK 2: User from another division CANNOT approve access requests
    # =========================================================================
    # Bob B1 submits access request
    req_res = requests.post(f"{BASE_URL}/access/request", headers=h_b1, json={
        "document_id": doc_id,
        "reason": "Need strategy to align project deliverables"
    })
    assert req_res.status_code == 201
    req_id = req_res.json()["request_id"]
    print(f"Submitted access request {req_id} by Bob B1")

    # Charlie (Division C) tries to approve -> Expected 403
    unauth_approve_c = requests.post(f"{BASE_URL}/access/approve", headers=h_c, json={
        "request_id": req_id,
        "decision": "approved"
    })
    print(f"Charlie (Division C) approval attempt status: {unauth_approve_c.status_code}")
    print(f"Response: {unauth_approve_c.text}")
    assert unauth_approve_c.status_code == 403, f"Expected 403, got {unauth_approve_c.status_code}"

    # Bob B1 (Division B, requester) tries to approve -> Expected 403
    unauth_approve_b = requests.post(f"{BASE_URL}/access/approve", headers=h_b1, json={
        "request_id": req_id,
        "decision": "approved"
    })
    assert unauth_approve_b.status_code == 403, f"Expected 403, got {unauth_approve_b.status_code}"
    print("[PASS] CHECK 2: Users cannot approve access requests belonging to another division (HTTP 403 Forbidden).")

    # =========================================================================
    # CHECK 3: Approved documents accessible ONLY to requesting user, not others in division
    # =========================================================================
    # Alice (Division A) approves Bob B1's request
    auth_approve = requests.post(f"{BASE_URL}/access/approve", headers=h_a, json={
        "request_id": req_id,
        "decision": "approved"
    })
    assert auth_approve.status_code == 200
    print("Alice approved Bob B1's request.")

    # Bob B1 (the requesting user) can access details and download
    b1_details = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=h_b1)
    assert b1_details.status_code == 200, f"Expected 200 for Bob B1, got {b1_details.status_code}"
    b1_dl = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=h_b1)
    assert b1_dl.status_code == 200, f"Expected 200 for Bob B1 download, got {b1_dl.status_code}"
    b1_list = requests.get(f"{BASE_URL}/documents", headers=h_b1).json()["documents"]
    assert any(d["id"] == doc_id for d in b1_list), "Doc should appear in Bob B1's document list"
    print("Bob B1 (requester) has full details, download, and listing access.")

    # Bob B2 (same Division B, but NOT the requester) MUST STILL BE FORBIDDEN
    b2_details = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=h_b2)
    assert b2_details.status_code == 403, f"Expected 403 for Bob B2 details, got {b2_details.status_code}"
    b2_dl = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=h_b2)
    assert b2_dl.status_code == 403, f"Expected 403 for Bob B2 download, got {b2_dl.status_code}"
    b2_list = requests.get(f"{BASE_URL}/documents", headers=h_b2).json()["documents"]
    assert not any(d["id"] == doc_id for d in b2_list), "Doc must NOT appear in Bob B2's document list"
    print("Bob B2 (colleague in Division B) received HTTP 403 for details, HTTP 403 for download, and document is NOT in their list.")
    print("[PASS] CHECK 3: Approved documents become accessible ONLY to the requesting user (Bob B1). Other users in that division (Bob B2) do NOT receive access.")

    # Clean up test document
    del_res = requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=h_a)
    assert del_res.status_code == 200
    print("Test document cleaned up.")

finally:
    print("Stopping Flask server...")
    server_process.terminate()
    server_process.wait()
    print("Flask server stopped.")
