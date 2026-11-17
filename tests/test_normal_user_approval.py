import subprocess
import time
import sys
import json
import uuid
import requests
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
python_exe = sys.executable

print("Starting Flask server for testing normal user approval scenario...")
server_process = subprocess.Popen(
    [python_exe, "run.py"],
    cwd=str(ROOT_DIR),
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
)

url_health = "http://127.0.0.1:5000/api/health/db"
started = False
for _ in range(30):
    try:
        r = requests.get(url_health, timeout=2)
        if r.status_code == 200:
            started = True
            print("Flask server started successfully on http://127.0.0.1:5000!")
            break
    except Exception:
        time.sleep(1)

if not started:
    print("FAILED: Flask server did not start in time.")
    server_process.terminate()
    sys.exit(1)

BASE_URL = "http://127.0.0.1:5000/api"

try:
    print("\n=========================================================================")
    print("   TESTING NORMAL USER APPROVAL SCENARIO (TRIAD AI ASSIGNMENT SPEC)    ")
    print("=========================================================================\n")

    suffix = uuid.uuid4().hex[:6]

    # 1. User A (Normal user in Division A, Uploader)
    email_a = f"usera_{suffix}@diva.com"
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "User A (Uploader)", "email": email_a, "password": "Password123!", "division": "Division A"
    })
    token_a = requests.post(f"{BASE_URL}/auth/login", json={"email": email_a, "password": "Password123!"}).json()["access_token"]
    h_a = {"Authorization": f"Bearer {token_a}"}
    print("[SETUP] 1. Created User A (normal user in Division A)")

    # 2. User B (Normal user in Division B, Requester)
    email_b = f"userb_{suffix}@divb.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "User B (Requester)", "email": email_b, "password": "Password123!", "division": "Division B"
    })
    token_b = requests.post(f"{BASE_URL}/auth/login", json={"email": email_b, "password": "Password123!"}).json()["access_token"]
    h_b = {"Authorization": f"Bearer {token_b}"}
    print("[SETUP] 2. Created User B (normal user in Division B, requester)")

    # 3. User C (Normal user in Division A - NOT an admin, NOT the uploader, NOT the requester)
    email_c = f"userc_{suffix}@diva.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "User C (Peer in Div A)", "email": email_c, "password": "Password123!", "division": "Division A"
    })
    me_c_res = requests.post(f"{BASE_URL}/auth/login", json={"email": email_c, "password": "Password123!"}).json()
    token_c = me_c_res["access_token"]
    user_c_role = me_c_res["user"]["role"]
    h_c = {"Authorization": f"Bearer {token_c}"}
    assert user_c_role == "user", f"Expected User C to be 'user', got {user_c_role}"
    print(f"[SETUP] 3. Created User C (normal user in Division A, role='{user_c_role}')")

    # 4. User D (Unrelated user in Division D)
    email_d = f"userd_{suffix}@divd.com"
    requests.post(f"{BASE_URL}/auth/register", json={
        "name": "User D (Unrelated Div D)", "email": email_d, "password": "Password123!", "division": "Division D"
    })
    token_d = requests.post(f"{BASE_URL}/auth/login", json={"email": email_d, "password": "Password123!"}).json()["access_token"]
    h_d = {"Authorization": f"Bearer {token_d}"}
    print("[SETUP] 4. Created User D (unrelated user in Division D)")

    # Step 1: User A uploads a document to Division A
    with open(ROOT_DIR / "test_sample.pdf", "rb") as f:
        pdf_bytes = f.read()

    upload_res = requests.post(
        f"{BASE_URL}/documents/upload",
        headers=h_a,
        data={
            "title": f"Div A Engineering Spec {suffix}",
            "description": "Division A internal document",
            "metadata": json.dumps({"Division": "Division A", "Report Type": "Technical"})
        },
        files={"file": ("spec.pdf", pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    doc_id = upload_res.json()["document_id"]
    print(f"\n[STEP 1] User A uploaded document {doc_id} to Division A.")

    # Step 2: User B in Division B requests access to User A's document
    req_res = requests.post(f"{BASE_URL}/access/request", headers=h_b, json={
        "document_id": doc_id,
        "reason": "Need technical spec for inter-division API integration."
    })
    assert req_res.status_code == 201, f"Access request failed: {req_res.text}"
    request_id = req_res.json()["request_id"]
    print(f"[STEP 2] User B requested access to Document {doc_id}. Request ID: {request_id}")

    # Before approval: Verify User B CANNOT download
    dl_before = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=h_b)
    assert dl_before.status_code == 403, f"Expected 403 before approval, got {dl_before.status_code}"
    print("  [VERIFIED] User B download blocked with HTTP 403 before approval.")

    # Step 7: Verify that the requester (User B) cannot approve their own request
    self_approve = requests.post(f"{BASE_URL}/access/approve", headers=h_b, json={
        "request_id": request_id,
        "decision": "approved"
    })
    assert self_approve.status_code == 403, f"Expected 403 for self-approval, got {self_approve.status_code}"
    print(f"[STEP 7 PASSED] Requester (User B) blocked from approving own request (HTTP 403): {self_approve.json().get('error')}")

    # Step 6: Verify that an unrelated Division D user cannot approve the request
    unrelated_approve = requests.post(f"{BASE_URL}/access/approve", headers=h_d, json={
        "request_id": request_id,
        "decision": "approved"
    })
    assert unrelated_approve.status_code == 403, f"Expected 403 for unrelated user, got {unrelated_approve.status_code}"
    print(f"[STEP 6 PASSED] Unrelated Division D user blocked from approving request (HTTP 403): {unrelated_approve.json().get('error')}")

    # Step 3 & 4: User C (NORMAL USER in Division A, not admin) attempts to approve User B's request
    print("\n[STEP 3 & 4] User C (normal non-admin user in Division A) attempting to approve request...")
    user_c_approve = requests.post(f"{BASE_URL}/access/approve", headers=h_c, json={
        "request_id": request_id,
        "decision": "approved"
    })
    print(f"User C approval status: {user_c_approve.status_code}")
    print(f"User C approval response: {user_c_approve.text}")
    assert user_c_approve.status_code == 200, f"Expected 200 for normal Division A user approval, got {user_c_approve.status_code}: {user_c_approve.text}"
    print("[STEP 4 PASSED] Normal user User C in Division A successfully approved the request!")

    # Step 5: Verify that approval succeeded and User B can download the document
    dl_after = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=h_b)
    assert dl_after.status_code == 200, f"Expected 200 for User B download post-approval, got {dl_after.status_code}"
    assert len(dl_after.content) > 0, "Downloaded file payload was empty!"
    print(f"[STEP 5 PASSED] User B successfully downloaded the document ({len(dl_after.content)} bytes) after User C's approval!")

    # Verify document details accessible to User B
    details_after = requests.get(f"{BASE_URL}/documents/{doc_id}", headers=h_b)
    assert details_after.status_code == 200
    print("  [VERIFIED] User B can also view document details post-approval.")

    # Cleanup test document
    del_res = requests.delete(f"{BASE_URL}/documents/{doc_id}", headers=h_a)
    assert del_res.status_code == 200
    print("\n[CLEANUP] Deleted test document.")

    print("\n=========================================================================")
    print("   ALL CHECKS PASSED: NORMAL USER APPROVAL WORKS FULLY AND SECURELY!   ")
    print("=========================================================================\n")

finally:
    print("Stopping Flask server...")
    server_process.terminate()
    server_process.wait()
    print("Server stopped.")
