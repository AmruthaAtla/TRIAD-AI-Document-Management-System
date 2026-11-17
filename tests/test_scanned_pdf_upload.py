import requests
import json

BASE_URL = "http://127.0.0.1:5000"

EMAIL = "testa20261116000728@example.com"
PASSWORD = "TestPass123"

# Login
login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={"email": EMAIL, "password": PASSWORD}
)

assert login.status_code == 200

token = login.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

metadata = {
    "Department": "Finance",
    "Project Name": "OCR Testing",
    "Financial Year": 2026,
    "Report Date": "2026-11-16"
}

# Upload scanned PDF
with open("tests/scanned_test.pdf", "rb") as file:

    response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        data={
            "title": "Scanned OCR Test",
            "metadata": json.dumps(metadata)
        },
        files={
            "file": ("scanned_test.pdf", file, "application/pdf")
        }
    )

print("Upload status:", response.status_code)
print("Response:", response.json())

assert response.status_code == 201

document_id = response.json()["document_id"]

print("\nDocument ID:", document_id)
print("Scanned PDF uploaded successfully!")