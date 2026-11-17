import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:5000"

# Login as admin
login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "testa20261116000728@example.com",
        "password": "TestPass123"
    }
)

print("Login:", login.status_code)

token = login.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

pdf_path = Path(__file__).resolve().parents[1] / "test_sample.pdf"


def test_upload(metadata, expected_status, test_name):

    with open(pdf_path, "rb") as pdf:

        response = requests.post(
            f"{BASE_URL}/api/documents/upload",
            headers=headers,
            data={
                "title": test_name,
                "metadata": metadata
            },
            files={
                "file": (
                    "test_sample.pdf",
                    pdf,
                    "application/pdf"
                )
            }
        )

    print(
        f"{test_name}: "
        f"Expected {expected_status}, "
        f"Received {response.status_code}"
    )

    print(response.json())

    assert response.status_code == expected_status

    # Delete successfully uploaded test document
    if response.status_code == 201:
        document_id = response.json()["document_id"]

        delete_response = requests.delete(
            f"{BASE_URL}/api/documents/{document_id}",
            headers=headers
        )

        print("Test document cleanup:", delete_response.status_code)


print("\n=== DYNAMIC METADATA FIELD TYPE TESTS ===")

# Test 1: All valid metadata values
test_upload(
    '{"Department":"Finance","Project Name":"ECU Platform",'
    '"Financial Year":2026,"Report Date":"2026-11-16"}',
    201,
    "All Valid Metadata"
)

# Test 2: Invalid text value
test_upload(
    '{"Department":"Finance","Project Name":123,'
    '"Financial Year":2026}',
    400,
    "Invalid Text"
)

# Test 3: Invalid number value
test_upload(
    '{"Department":"Finance","Project Name":"ECU Platform",'
    '"Financial Year":"ABC"}',
    400,
    "Invalid Number"
)

# Test 4: Invalid date format
test_upload(
    '{"Department":"Finance","Project Name":"ECU Platform",'
    '"Financial Year":2026,"Report Date":"16/11/2026"}',
    400,
    "Invalid Date"
)

print("\n=== TESTING COMPLETED ===")