import requests

BASE_URL = "http://127.0.0.1:5000"

login = requests.post(
    f"{BASE_URL}/api/auth/login",
    json={
        "email": "testa20261116000728@example.com",
        "password": "TestPass123"
    }
)

assert login.status_code == 200

token = login.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}"
}

fields = [
    {
        "field_name": "Division",
        "field_type": "text",
        "required": False
    },
    {
        "field_name": "Report Type",
        "field_type": "text",
        "required": False
    }
]

for field in fields:
    response = requests.post(
        f"{BASE_URL}/api/admin/metadata",
        headers=headers,
        json=field
    )

    print(field["field_name"], response.status_code, response.text)