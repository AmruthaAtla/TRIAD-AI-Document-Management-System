import fitz
import pytesseract

from PIL import Image
from io import BytesIO


# Windows Tesseract installation path
pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


def extract_text_from_pdf(file_stream):
    try:
        pdf_bytes = file_stream.read()

        document = fitz.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        extracted_text = []

        for page_number, page in enumerate(document):

            # Step 1: Extract selectable PDF text
            text = page.get_text("text").strip()

            # Step 2: If no selectable text exists, use OCR
            if not text:

                pix = page.get_pixmap(
                    matrix=fitz.Matrix(2, 2),
                    alpha=False
                )

                image = Image.open(
                    BytesIO(pix.tobytes("png"))
                )

                text = pytesseract.image_to_string(
                    image,
                    lang="eng"
                ).strip()

            extracted_text.append(text)

        document.close()

        return "\n".join(extracted_text).strip()

    except Exception:
        raise


def extract_text_from_image(file_stream):
    try:
        image_bytes = file_stream.read()
        image = Image.open(BytesIO(image_bytes))

        # Convert palette/alpha modes to RGB for Tesseract OCR
        if image.mode not in ("L", "RGB"):
            image = image.convert("RGB")

        text = pytesseract.image_to_string(
            image,
            lang="eng"
        ).strip()

        return text

    except Exception:
        raise


def extract_text_from_txt(file_stream):
    try:
        raw_bytes = file_stream.read()
        return raw_bytes.decode("utf-8", errors="replace").strip()
    except Exception:
        raise


def extract_text(file_stream, extension):
    ext = (extension or "").lower()
    if ext == "pdf":
        return extract_text_from_pdf(file_stream)
    elif ext in {"png", "jpg", "jpeg"}:
        return extract_text_from_image(file_stream)
    elif ext == "txt":
        return extract_text_from_txt(file_stream)
    return ""
