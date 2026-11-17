from app import extensions
from werkzeug.utils import secure_filename


def upload_file(file, uploaded_by):
    if not file or not file.filename:
        raise ValueError("No file selected")

    filename = secure_filename(file.filename)

    if not filename:
        raise ValueError("Invalid filename")

    file_id = extensions.gridfs_bucket.upload_from_stream(
        filename,
        file.stream,
        metadata={
            "uploaded_by": str(uploaded_by),
            "content_type": file.content_type
        }
    )

    return str(file_id)


def download_file(file_id):
    from bson import ObjectId

    if not ObjectId.is_valid(file_id):
        return None

    try:
        return extensions.gridfs_bucket.open_download_stream(
            ObjectId(file_id)
        )
    except Exception:
        return None


def delete_file(file_id):
    from bson import ObjectId

    if not ObjectId.is_valid(file_id):
        return False

    try:
        extensions.gridfs_bucket.delete(ObjectId(file_id))
        return True
    except Exception:
        return False