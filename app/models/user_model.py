from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User:
    @staticmethod
    def create_user(name, email, password, division, role="user"):
        user = {
            "name": name,
            "email": email.lower().strip(),
            "password": generate_password_hash(password),
            "division": division,
            "role": role,
            "created_at": datetime.now(timezone.utc)
        }

        result = db.users.insert_one(user)
        return str(result.inserted_id)

    @staticmethod
    def find_by_email(email):
        return db.users.find_one({
            "email": email.lower().strip()
        })

    @staticmethod
    def verify_password(user, password):
        return check_password_hash(
            user["password"],
            password
        )