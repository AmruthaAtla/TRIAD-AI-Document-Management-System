import io
import zipfile

from PIL import Image


ALLOWED_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "txt", "docx"
}


def validate_file(file, filename):

    # Step 1: Check filename extension
    if "." not in filename:
        return False, "File must have an extension"

    extension = filename.rsplit(".", 1)[-1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        return False, "Unsupported file format"

    # Step 2: Read file content
    file_content = file.read()

    # Reset stream for later storage
    file.seek(0)

    if not file_content:
        return False, "Empty files are not allowed"

    # Step 3: Validate PDF
    if extension == "pdf":
        if not file_content.startswith(b"%PDF-"):
            return False, "Invalid PDF file"

    # Step 4: Validate PNG and JPEG
    elif extension in {"png", "jpg", "jpeg"}:
        try:
            image = Image.open(io.BytesIO(file_content))
            image.verify()

            if extension == "png" and image.format != "PNG":
                return False, "File content does not match PNG extension"

            if extension in {"jpg", "jpeg"} and image.format != "JPEG":
                return False, "File content does not match JPEG extension"

        except Exception:
            return False, "Invalid image file"

    # Step 5: Validate TXT
    elif extension == "txt":
        try:
            file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False, "Invalid text file encoding"

    # Step 6: Validate DOCX
    elif extension == "docx":
        try:
            with zipfile.ZipFile(io.BytesIO(file_content)) as docx:
                if (
                    "[Content_Types].xml" not in docx.namelist()
                    or "word/document.xml" not in docx.namelist()
                ):
                    return False, "Invalid DOCX file"

        except zipfile.BadZipFile:
            return False, "Invalid DOCX file"

    return True, "File format validated successfully"