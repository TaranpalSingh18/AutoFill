from fastapi import APIRouter, UploadFile, File as FastAPIFile, HTTPException
import json
from bson.binary import Binary
from datetime import datetime, timezone, timedelta
from db.database import db
from models.file import Section, File as FileModel
from uuid import uuid4

upload_router = APIRouter(tags=["upload-file"], prefix="/upload")

uploads = db["files"]


@upload_router.post('', response_model=FileModel)
async def upload_file(file: UploadFile = FastAPIFile(...)):

    if not file:
        raise HTTPException(status_code=404, detail="file not found")

    payload = await file.read()

    file_data = FileModel(
        file_id=str(uuid4()),
        name = file.filename or "file_{file_id}",
        file_length=len(payload)
    )

    uploads.insert_one({
        **file_data.model_dump(),
        "content_type": file.content_type,
        "upload_time": datetime.now(timezone.utc),
        # "content": Binary(payload),
    })
    return file_data
    



