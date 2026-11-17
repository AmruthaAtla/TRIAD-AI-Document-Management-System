import requests

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

# Search for text present only inside the scanned PDF
response = requests.get(
    f"{BASE_URL}/api/search",
    headers=headers,
    #params={"q": "Tesseract extracts text"}
    params={"q": "Scanned PDF OCR Testing Successful"}
)

print("Search status:", response.status_code)
print("Content-Type:", response.headers.get("Content-Type"))
print("Search response:")
print(response.text)