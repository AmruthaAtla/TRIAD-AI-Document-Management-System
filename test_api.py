import os
import json
import uuid
import requests

BASE_URL = "http://127.0.0.1:5000/api"
REPORT_FILE = "test_report.txt"

results = {
    "total": 0,
    "passed": 0,
    "failed": 0,
    "errors": []
}


def log_result(test_name, success, error_msg=""):
    results["total"] += 1

    if success:
        results["passed"] += 1
        print(f"[PASS] {test_name}")
    else:
        results["failed"] += 1
        results["errors"].append(
            f"[{test_name}] FAILED: {error_msg}"
        )
        print(f"[FAIL] {test_name}: {error_msg}")


def create_test_user():
    """Register a unique user for automated testing."""

    unique_id = uuid.uuid4().hex[:8]

    user_data = {
        "name": "Automated Test User",
        "email": f"test_{unique_id}@example.com",
        
        "password": "Test@12345",
        "division": "Engineering"
    }
    print("Test Email:", user_data["email"])

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json=user_data,
            timeout=20
        )

        if response.status_code not in [200, 201]:
            log_result(
                "User Registration",
                False,
                response.text
            )
            return None

        log_result("User Registration", True)
        return user_data

    except requests.RequestException as error:
        log_result("User Registration", False, str(error))
        return None


def login_test_user(user_data):
    """Login and obtain JWT authentication token."""

    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "email": user_data["email"],
                "password": user_data["password"]
            },
            timeout=20
        )

        if response.status_code != 200:
            log_result(
                "User Login",
                False,
                response.text
            )
            return None

        token = response.json().get("access_token")

        if not token:
            log_result(
                "User Login",
                False,
                "Access token missing"
            )
            return None

        log_result("User Login", True)
        return token

    except requests.RequestException as error:
        log_result("User Login", False, str(error))
        return None


def test_document_upload(token):

    file_path = "test_sample.pdf"

    if not os.path.exists(file_path):
        log_result(
            "Document Upload",
            False,
            "test_sample.pdf not found in project root"
        )
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    data = {
    "title": "Automated Financial Test Report",
    "metadata": json.dumps({
        "Division": "Engineering",
        "Report Type": "Financial"
    })
}

    try:
        with open(file_path, "rb") as pdf_file:

            files = {
                "file": (
                    "test_sample.pdf",
                    pdf_file,
                    "application/pdf"
                )
            }

            response = requests.post(
                f"{BASE_URL}/documents/upload",
                headers=headers,
                data=data,
                files=files,
                timeout=60
            )

        if response.status_code in [200, 201]:
            log_result("POST /api/documents/upload", True)
            print("Upload Response:", response.json())

        else:
            log_result(
                "POST /api/documents/upload",
                False,
                f"Expected 200/201, got {response.status_code}: "
                f"{response.text}"
            )

    except Exception as error:
        log_result(
            "POST /api/documents/upload",
            False,
            str(error)
        )


def generate_report():

    with open(REPORT_FILE, "w", encoding="utf-8") as report:

        report.write("=== TRIAD AI DMS API TEST REPORT ===\n\n")

        report.write(
            f"Total Tests: {results['total']}\n"
        )

        report.write(
            f"Passed: {results['passed']}\n"
        )

        report.write(
            f"Failed: {results['failed']}\n\n"
        )

        if results["errors"]:

            report.write("=== FAILURE DETAILS ===\n")

            for error in results["errors"]:
                report.write(error + "\n")


if __name__ == "__main__":

    print("Starting Triad AI DMS automated tests...")

    user = create_test_user()

    if user:
        token = login_test_user(user)

        if token:
            test_document_upload(token)

    generate_report()

    print("\nTesting completed.")
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    print(f"Report saved to {REPORT_FILE}")