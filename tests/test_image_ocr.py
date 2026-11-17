import io
import json
import time
import requests
from PIL import Image, ImageDraw

BASE_URL = "http://127.0.0.1:5000"

def run_test():
    # Wait for server ready
    for _ in range(10):
        try:
            r = requests.get(f"{BASE_URL}/")
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(1)

    print("Server is responsive. Testing standalone image OCR...")

    # 1. Register a test user
    email = f"ocr_img_user_{int(time.time())}@example.com"
    reg_res = requests.post(f"{BASE_URL}/api/auth/register", json={
        "name": "Image OCR Tester",
        "email": email,
        "password": "Password123!",
        "division": "Engineering"
    })
    assert reg_res.status_code == 201, f"Reg failed: {reg_res.text}"

    # 2. Login
    login_res = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200, f"Login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create a test PNG image containing unique visible text
    img = Image.new("RGB", (320, 80), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    target_text = "SECRET_QUARTERLY_EARNINGS"
    draw.text((10, 25), target_text, fill=(0, 0, 0))

    img_buf = io.BytesIO()
    img.save(img_buf, format="PNG")
    img_buf.seek(0)

    # 4. Upload standalone PNG image
    upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        data={
            "title": "Quarterly Financial PNG",
            "description": "Standalone image upload",
            "metadata": json.dumps({"Division": "Engineering", "Report Type": "Financial"})
        },
        files={"file": ("earnings_chart.png", img_buf, "image/png")}
    )
    assert upload_res.status_code == 201, f"Upload failed: {upload_res.text}"
    doc_id = upload_res.json()["document_id"]
    print(f"[PASS] PNG Image uploaded successfully with document_id: {doc_id}")

    # 5. Fetch document details to verify OCR text
    details_res = requests.get(f"{BASE_URL}/api/documents/{doc_id}", headers=headers)
    assert details_res.status_code == 200, f"Details failed: {details_res.text}"
    doc_payload = details_res.json().get("document", {})
    ocr_text = doc_payload.get("ocr_text", "")
    print(f"Extracted Image OCR Text: '{ocr_text}'")
    assert "SECRET" in ocr_text or "QUARTERLY" in ocr_text or "EARNINGS" in ocr_text, f"OCR text did not match: '{ocr_text}'"
    print("[PASS] Standalone Image OCR text extraction verified in Document Details!")

    # 6. Search across OCR-extracted text
    search_res = requests.get(f"{BASE_URL}/api/search?q=EARNINGS", headers=headers)
    assert search_res.status_code == 200, f"Search failed: {search_res.text}"
    results = search_res.json().get("results", [])
    assert any(d["id"] == doc_id for d in results), f"Document {doc_id} not found in search results: {results}"
    print("[PASS] Standalone Image OCR full-text search verified!")

    # 7. Also test a standalone JPG image
    jpg_img = Image.new("RGB", (320, 80), color=(255, 255, 255))
    jpg_draw = ImageDraw.Draw(jpg_img)
    jpg_draw.text((10, 25), "SPECIAL_AUDIT_REPORT_2026", fill=(0, 0, 0))
    jpg_buf = io.BytesIO()
    jpg_img.save(jpg_buf, format="JPEG")
    jpg_buf.seek(0)

    jpg_upload_res = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        data={
            "title": "Audit JPG Document",
            "description": "Standalone JPG image upload",
            "metadata": json.dumps({"Division": "Engineering", "Report Type": "Audit"})
        },
        files={"file": ("audit_page.jpg", jpg_buf, "image/jpeg")}
    )
    assert jpg_upload_res.status_code == 201, f"JPG Upload failed: {jpg_upload_res.text}"
    jpg_doc_id = jpg_upload_res.json()["document_id"]
    print(f"[PASS] JPG Image uploaded successfully with document_id: {jpg_doc_id}")

    jpg_details_res = requests.get(f"{BASE_URL}/api/documents/{jpg_doc_id}", headers=headers).json()
    jpg_doc_payload = jpg_details_res.get("document", {})
    jpg_ocr = jpg_doc_payload.get("ocr_text", "")
    print(f"Extracted JPG OCR Text: '{jpg_ocr}'")
    assert "AUDIT" in jpg_ocr or "REPORT" in jpg_ocr or "2026" in jpg_ocr, f"JPG OCR text did not match: '{jpg_ocr}'"
    print("[PASS] Standalone JPG Image OCR text extraction verified!")

    print("\nALL STANDALONE IMAGE OCR TESTS PASSED!")

if __name__ == "__main__":
    run_test()
