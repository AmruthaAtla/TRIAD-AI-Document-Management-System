import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, extensions
from flask_jwt_extended import create_access_token
from bson import ObjectId

app = create_app()
client = app.test_client()
db = extensions.db

def run_tests():
    print("=== Testing Metadata Access Permissions ===")

    # Setup test users
    db.users.delete_many({"email": {"$in": ["test_normal_meta@test.com", "test_admin_meta@test.com"]}})

    normal_user = {
        "name": "Normal Meta User",
        "email": "test_normal_meta@test.com",
        "password": "hashed_password_dummy",
        "division": "Engineering",
        "role": "user"
    }
    normal_id = db.users.insert_one(normal_user).inserted_id

    admin_user = {
        "name": "Admin Meta User",
        "email": "test_admin_meta@test.com",
        "password": "hashed_password_dummy",
        "division": "Engineering",
        "role": "admin"
    }
    admin_id = db.users.insert_one(admin_user).inserted_id

    with app.app_context():
        normal_token = create_access_token(
            identity=str(normal_id),
            additional_claims={"role": "user", "division": "Engineering"}
        )
        admin_token = create_access_token(
            identity=str(admin_id),
            additional_claims={"role": "admin", "division": "Engineering"}
        )

    # 1. Unauthenticated GET /api/admin/metadata -> 401
    res1 = client.get("/api/admin/metadata")
    assert res1.status_code == 401, f"Expected 401, got {res1.status_code}"
    print("[PASS] Unauthenticated GET /api/admin/metadata returned 401")

    # 2. Normal user GET /api/admin/metadata -> 200
    res2 = client.get("/api/admin/metadata", headers={"Authorization": f"Bearer {normal_token}"})
    assert res2.status_code == 200, f"Expected 200, got {res2.status_code}: {res2.get_json()}"
    data2 = res2.get_json()
    assert "metadata_fields" in data2
    print(f"[PASS] Normal user GET /api/admin/metadata returned 200 with {data2['total']} fields")

    # 3. Admin user GET /api/admin/metadata -> 200
    res3 = client.get("/api/admin/metadata", headers={"Authorization": f"Bearer {admin_token}"})
    assert res3.status_code == 200, f"Expected 200, got {res3.status_code}"
    print(f"[PASS] Admin user GET /api/admin/metadata returned 200")

    # 4. Normal user POST /api/admin/metadata -> 403 Forbidden
    res4 = client.post(
        "/api/admin/metadata",
        headers={"Authorization": f"Bearer {normal_token}"},
        json={"field_name": "TestField", "field_type": "text", "required": False}
    )
    assert res4.status_code == 403, f"Expected 403, got {res4.status_code}: {res4.get_json()}"
    print("[PASS] Normal user POST /api/admin/metadata correctly blocked with 403")

    # Clean up test users
    db.users.delete_many({"_id": {"$in": [normal_id, admin_id]}})
    print("\nALL METADATA ACCESS TESTS PASSED!")

if __name__ == "__main__":
    run_tests()
