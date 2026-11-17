import os
from pathlib import Path
from dotenv import load_dotenv

# Locate the project root directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Load environment variables
load_dotenv(BASE_DIR / ".env")


class Config:

    SECRET_KEY = os.getenv("SECRET_KEY")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")

    MONGO_URI = os.getenv("MONGO_URI")

    DATABASE_NAME = os.getenv(
        "DATABASE_NAME",
        "triad_dms"
    )

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024

    JWT_ACCESS_TOKEN_EXPIRES = 3600

    @staticmethod
    def validate():

        required_variables = [
            "SECRET_KEY",
            "JWT_SECRET_KEY",
            "MONGO_URI"
        ]

        missing = [
            variable
            for variable in required_variables
            if not os.getenv(variable)
        ]

        if missing:
            raise ValueError(
                f"Missing environment variables: {missing}"
            )