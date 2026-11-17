import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app import create_app, extensions

app = create_app()

db = extensions.db

document = db.documents.find_one(
    {"title": "Scanned OCR Test"},
    sort=[("uploaded_at", -1)]
)

if document:
    print("Document found:", document["title"])
    print("Filename:", document["filename"])
    print("Division:", document["division"])

    ocr_text = document.get("ocr_text", "")

    print("\nOCR text length:", len(ocr_text))
    print("Stored OCR text:")
    print(ocr_text)

else:
    print("Document not found in MongoDB")