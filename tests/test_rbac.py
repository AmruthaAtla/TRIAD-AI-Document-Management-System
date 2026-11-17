
import requests

BASE_URL = "http://127.0.0.1:5000"

# Use the login details created earlier
login_data = {
    "email": "testA20261116000728@example.com",
    "password": "TestPass123"
}

response = requests.post(
    f"{BASE_URL}/api/auth/login",
    json=login_data
)

response.raise_for_status()
token = response.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

with open("test_sample.pdf", "rb") as pdf:
    files = {
        "file": ("test_sample.pdf", pdf, "application/pdf")
    }

    data = {
        "title": "Division A Test Document",
        "metadata": '{"Division":"Division A","Report Type":"Financial"}'
    }

    upload_response = requests.post(
        f"{BASE_URL}/api/documents/upload",
        headers=headers,
        files=files,
        data=data
    )

print("Upload status:", upload_response.status_code)
print("Upload response:", upload_response.text)
