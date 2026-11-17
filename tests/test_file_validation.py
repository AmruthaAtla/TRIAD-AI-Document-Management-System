
import requests
import json
import tempfile
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"

EMAIL = "testa20261116000728@example.com"
PASSWORD = "TestPass123"

# Login as User A
login_response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": EMAIL, "password": PASSWORD}
)

##assert login_response.status_code == 200, "Login failed"
print("Login status:", login_response.status_code)
print("Login response:", login_response.text)

assert login_response.status_code == 200, "Login failed"

token = login_response.json()["access_token"]

headers = {"Authorization": f"Bearer {token}"}

valid_pdf = Path(__file__).resolve().parents[1] / "test_sample.pdf"


def upload_test(filename, content, expected_status, title):
    metadata = {
        "Department": "Finance",
        "Project Name": "Test Project",
        "Financial Year": 2026,
        "Report Date": "2026-11-16"
    }

    response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        data={
            "title": title,
            "metadata": json.dumps(metadata)
        },
        files={
            "file": (filename, content)
        }
    )

    passed = response.status_code == expected_status

    print(
        f"{'PASS' if passed else 'FAIL'} | "
        f"{title} | "
        f"Expected: {expected_status}, "
        f"Received: {response.status_code} | "
        f"{response.json()}"
    )

    return response

print("\n=== FILE FORMAT VALIDATION TESTS ===\n")

# Test 1: Genuine PDF
with open(valid_pdf, "rb") as file:
    response = upload_test(
        "valid_test.pdf",
        file,
        201,
        "Valid PDF"
    )

    # Clean up the uploaded test document
    if response.status_code == 201:
        document_id = response.json()["document_id"]

        requests.delete(
            f"{BASE_URL}/api/documents/{document_id}",
            headers=headers
        )

# Test 2: Unsupported extension
upload_test(
    "malicious.exe",
    b"sample executable content",
    400,
    "Unsupported format"
)

# Test 3: Fake PDF
upload_test(
    "fake.pdf",
    b"This is not a PDF file",
    400,
    "Fake PDF"
)

# Test 4: Empty PDF
upload_test(
    "empty.pdf",
    b"",
    400,
    "Empty file"
)

# Test 5: Invalid DOCX
upload_test(
    "fake.docx",
    b"This is not a Word document",
    400,
    "Invalid DOCX"
)

print("\n=== TESTING COMPLETED ===")
