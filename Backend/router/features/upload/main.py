from fastapi import APIRouter, UploadFile, File as FastAPIFile, HTTPException
import os
from datetime import datetime, timezone
from uuid import uuid4

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from db.database import db
from models.file import File as FileModel

upload_router = APIRouter(tags=["upload-file"], prefix="/upload")
uploads = db["files"]

_cloudinary_configured = False


def configure_cloudinary() -> None:
    global _cloudinary_configured
    if _cloudinary_configured:
        return

    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url, secure=True)
        _cloudinary_configured = True
        return

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all([cloud_name, api_key, api_secret]):
        raise RuntimeError(
            "Cloudinary is not configured. Set CLOUDINARY_URL or CLOUDINARY_CLOUD_NAME/API_KEY/API_SECRET."
        )

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )
    _cloudinary_configured = True


@upload_router.post("", response_model=FileModel)
async def upload_file(file: UploadFile = FastAPIFile(...)):
    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="empty file")

    file_id = str(uuid4())
    file_name = (file.filename or f"file_{file_id}").strip()

    try:
        configure_cloudinary()
        upload_result = cloudinary.uploader.upload(
            payload,
            resource_type="auto",
            folder="autofill_uploads",
            public_id=file_id,
            overwrite=False,
            filename_override=file_name,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except CloudinaryError as e:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {str(e)}")

    file_data = FileModel(
        file_id=file_id,
        name=file_name,
        file_length=len(payload),
    )

    uploads.insert_one(
        {
            **file_data.model_dump(),
            "content_type": file.content_type,
            "upload_time": datetime.now(timezone.utc),
            "cloudinary_public_id": upload_result.get("public_id"),
            "cloudinary_url": upload_result.get("secure_url"),
            "cloudinary_bytes": upload_result.get("bytes"),
            "cloudinary_format": upload_result.get("format"),
            "cloudinary_resource_type": upload_result.get("resource_type"),
        }
    )

    return file_data