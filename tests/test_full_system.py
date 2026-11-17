import sys
import json
from pathlib import Path
from io import BytesIO

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, extensions
from bson import ObjectId

app = create_app()
client = app.test_client()
db = extensions.db

passed_count = 0
failed_count = 0

def check(condition, test_name, extra=""):
    global passed_count, failed_count
    if condition:
        passed_count += 1
        print(f"[PASS] {test_name}")
    else:
        failed_count += 1
        print(f"[FAIL] {test_name}: {extra}")
        assert False, f"{test_name} failed: {extra}"

def run_regression_suite():
    global passed_count, failed_count
    print("\n=======================================================")
    print("   TRIAD AI DMS - FULL END-TO-END REGRESSION SUITE   ")
    print("=======================================================\n")

    # Clean up test users
    db.users.delete_many({"email": {"$in": [
        "user_div_a@triad.com",
        "user_div_b@triad.com",
        "admin_div_a@triad.com"
    ]}})

    # 1. Registration
    res = client.post("/api/auth/register", json={
        "name": "User Division A",
        "email": "user_div_a@triad.com",
        "password": "Password123!",
        "division": "Division A"
    })
    check(res.status_code == 201, "1.1 Normal User Registration (Division A)")
    user_a_id = res.get_json()["user_id"]

    res = client.post("/api/auth/register", json={
        "name": "User Division B",
        "email": "user_div_b@triad.com",
        "password": "Password123!",
        "division": "Division B"
    })
    check(res.status_code == 201, "1.2 Normal User Registration (Division B)")
    user_b_id = res.get_json()["user_id"]

    res = client.post("/api/auth/register", json={
        "name": "Admin Division A",
        "email": "admin_div_a@triad.com",
        "password": "Password123!",
        "division": "Division A"
    })
    check(res.status_code == 201, "1.3 Admin User Registration")
    admin_a_id = res.get_json()["user_id"]
    db.users.update_one({"_id": ObjectId(admin_a_id)}, {"$set": {"role": "admin"}})

    # 2. Login
    res_a = client.post("/api/auth/login", json={"email": "user_div_a@triad.com", "password": "Password123!"})
    check(res_a.status_code == 200, "2.1 User A Login")
    token_a = res_a.get_json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    res_b = client.post("/api/auth/login", json={"email": "user_div_b@triad.com", "password": "Password123!"})
    check(res_b.status_code == 200, "2.2 User B Login")
    token_b = res_b.get_json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    res_admin = client.post("/api/auth/login", json={"email": "admin_div_a@triad.com", "password": "Password123!"})
    check(res_admin.status_code == 200, "2.3 Admin Login")
    token_admin = res_admin.get_json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {token_admin}"}

    # 3. Metadata creation & retrieval
    # Normal user cannot create metadata
    res = client.post("/api/admin/metadata", headers=headers_a, json={
        "field_name": "TestRestricted", "field_type": "text", "required": False
    })
    check(res.status_code == 403, "3.1 Normal user blocked from POST /api/admin/metadata")

    # Normal user CAN read metadata
    res = client.get("/api/admin/metadata", headers=headers_a)
    check(res.status_code == 200 and "metadata_fields" in res.get_json(), "3.2 Normal user can READ metadata configs")

    # 4. Upload with description and dynamic metadata
    sample_pdf_path = ROOT_DIR / "test_sample.pdf"
    with open(sample_pdf_path, "rb") as f:
        pdf_bytes = f.read()

    meta_payload = {
        "Department": "Engineering",
        "Project Name": "Alpha Project",
        "Financial Year": 2026,
        "Report Date": "2026-11-17"
    }

    upload_res = client.post(
        "/api/documents/upload",
        headers=headers_a,
        data={
            "title": "Division A Confidential Roadmap",
            "description": "Quarterly operational roadmap for Division A engineering.",
            "metadata": json.dumps(meta_payload),
            "file": (BytesIO(pdf_bytes), "roadmap.pdf")
        },
        content_type="multipart/form-data"
    )
    check(upload_res.status_code == 201, "4.1 Document Upload with Metadata & Description")
    doc_a_id = upload_res.get_json()["document_id"]

    # 5. Verify Document Details & Description Persistence
    details_res = client.get(f"/api/documents/{doc_a_id}", headers=headers_a)
    check(details_res.status_code == 200, "5.1 Owner can view Document Details")
    doc_data = details_res.get_json()["document"]
    check(doc_data.get("description") == "Quarterly operational roadmap for Division A engineering.", "5.2 Description properly persisted and serialized")
    check("ocr_text" in doc_data, "5.3 OCR text field returned in Document Details")

    # 6. Verify Division Isolation: User B cannot view or download Doc A
    unauth_details = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
    check(unauth_details.status_code == 403, "6.1 Cross-Division User B blocked from viewing Doc A Details (403)")

    unauth_dl = client.get(f"/api/documents/{doc_a_id}/download", headers=headers_b)
    check(unauth_dl.status_code == 403, "6.2 Cross-Division User B blocked from downloading Doc A (403)")

    # 7. Document Listing & Filtering
    list_res_a = client.get("/api/documents", headers=headers_a)
    check(list_res_a.status_code == 200 and list_res_a.get_json()["total"] >= 1, "7.1 User A can list Division A documents")

    list_res_b = client.get("/api/documents", headers=headers_b)
    check(list_res_b.status_code == 200 and not any(d["id"] == doc_a_id for d in list_res_b.get_json()["documents"]), "7.2 User B does NOT see Doc A in their document listing")

    # 8. Search & Secure Cross-Division Discovery
    # User A searches for "Confidential" -> has_access: True
    search_a = client.get("/api/search?q=Confidential", headers=headers_a)
    check(search_a.status_code == 200 and search_a.get_json()["total"] >= 1, "8.1 User A finds Doc A in search")
    found_a = [r for r in search_a.get_json()["results"] if r["id"] == doc_a_id][0]
    check(found_a.get("has_access") is True, "8.2 Search result has_access is True for division member")

    # User B searches for "Confidential" -> Secure Discovery: has_access: False, no OCR text exposed
    search_b = client.get("/api/search?q=Confidential", headers=headers_b)
    check(search_b.status_code == 200 and search_b.get_json()["total"] >= 1, "8.3 User B discovers Doc A header in cross-division search")
    found_b = [r for r in search_b.get_json()["results"] if r["id"] == doc_a_id][0]
    check(found_b.get("has_access") is False, "8.4 Discovered Doc A has has_access=False for User B")
    check("ocr_text" not in found_b, "8.5 OCR content is NOT exposed to User B")

    # 9. Cross-Division Access Request
    # User B requests access to Doc A
    req_res = client.post("/api/access/request", headers=headers_b, json={
        "document_id": doc_a_id,
        "reason": "Need roadmap to align cross-team infrastructure deliverables."
    })
    check(req_res.status_code == 201, "9.1 User B submits cross-division access request")
    req_id = req_res.get_json()["request_id"]

    # 10. View Incoming & Outgoing Requests
    # User A views incoming requests for Division A
    incoming_res = client.get("/api/access/requests?type=incoming", headers=headers_a)
    check(incoming_res.status_code == 200 and any(r["request_id"] == req_id for r in incoming_res.get_json()["requests"]), "10.1 User A sees pending incoming request")

    # User B views outgoing requests
    outgoing_res = client.get("/api/access/requests?type=outgoing", headers=headers_b)
    check(outgoing_res.status_code == 200 and any(r["request_id"] == req_id and r["status"] == "pending" for r in outgoing_res.get_json()["requests"]), "10.2 User B sees their outgoing request with status pending")

    # 11. Approval Workflow
    # User A approves the request
    approve_res = client.post("/api/access/approve", headers=headers_a, json={
        "request_id": req_id,
        "decision": "approved"
    })
    check(approve_res.status_code == 200 and approve_res.get_json()["status"] == "approved", "11.1 User A approves access request")

    # 12. Verified Access Post-Approval
    # User B can now view details!
    approved_details = client.get(f"/api/documents/{doc_a_id}", headers=headers_b)
    check(approved_details.status_code == 200, "12.1 User B can view details of Doc A after approval")

    # User B can now download!
    approved_dl = client.get(f"/api/documents/{doc_a_id}/download", headers=headers_b)
    check(approved_dl.status_code == 200 and len(approved_dl.data) > 0, "12.2 User B can download Doc A after approval")

    # Doc A now appears in User B's document listing!
    updated_list_b = client.get("/api/documents", headers=headers_b)
    check(any(d["id"] == doc_a_id for d in updated_list_b.get_json()["documents"]), "12.3 Approved cross-division document appears in User B's documents list")

    # 13. Document Deletion Permissions
    # User B cannot delete Doc A
    unauth_del = client.delete(f"/api/documents/{doc_a_id}", headers=headers_b)
    check(unauth_del.status_code == 403, "13.1 User B (non-owner, non-admin) blocked from deleting Doc A (403)")

    # User A (owner) deletes Doc A
    auth_del = client.delete(f"/api/documents/{doc_a_id}", headers=headers_a)
    check(auth_del.status_code == 200, "13.2 Owner User A successfully deleted Doc A")

    # Verify doc deleted
    deleted_check = client.get(f"/api/documents/{doc_a_id}", headers=headers_a)
    check(deleted_check.status_code == 404, "13.3 Document correctly removed (404)")

    # Clean up test users
    db.users.delete_many({"_id": {"$in": [ObjectId(user_a_id), ObjectId(user_b_id), ObjectId(admin_a_id)]}})
    db.access_requests.delete_many({"document_id": ObjectId(doc_a_id)})

    print("\n=======================================================")
    print(f"   ALL {passed_count} REGRESSION TESTS PASSED! (Failed: {failed_count})")
    print("=======================================================\n")

if __name__ == "__main__":
    run_regression_suite()
