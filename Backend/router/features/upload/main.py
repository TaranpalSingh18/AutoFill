from fastapi import APIRouter, UploadFile, File as FastAPIFile, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import os
from io import BytesIO
from datetime import datetime, timezone
from uuid import uuid4
from jose import jwt
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from pypdf import PdfReader
from docx import Document

from db.database import db
from Chunking.semantic_chunking import parse_resume_text
from Chunking.llm_reviewer import review_needs_review_chunks
from router.features.retrieval.vector_db import ingest_semantic_chunks
upload_router = APIRouter(tags=["files"], prefix="/files")
files_collection = db["files"]

oath2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")
secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGO")


def resolve_cloudinary_resource_type(filename: str, content_type: str | None) -> str:
    """Determine Cloudinary resource type based on file extension or content-type"""
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")

    if content_type and content_type.startswith("image/"):
        return "image"

    if ext in {"pdf", "doc", "docx", "xls", "xlsx", "txt", "csv"}:
        return "raw"

    return "auto"


def get_cloudinary_folder(filename: str, content_type: str | None) -> str:
    """Determine Cloudinary folder based on file type"""
    resource_type = resolve_cloudinary_resource_type(filename, content_type)
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "").lower()
    
    # Organize by file type
    if content_type and content_type.startswith("image/"):
        return "autofill/images"
    elif ext in {"pdf"}:
        return "autofill/documents/pdf"
    elif ext in {"doc", "docx"}:
        return "autofill/documents/word"
    elif ext in {"xls", "xlsx"}:
        return "autofill/documents/excel"
    elif ext in {"txt", "csv"}:
        return "autofill/documents/text"
    else:
        return "autofill/documents/other"

def get_user_from_token(token: str = Depends(oath2_schema)):
    """Extract user from JWT token"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        email = payload.get("sub")
        return email
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def extract_text_from_file(file_content: bytes, filename: str, content_type: str | None) -> str:
    """Extract raw text from supported document types for downstream semantic chunking."""
    ext = (filename.rsplit(".", 1)[-1].lower() if "." in filename else "")

    if ext == "pdf" or (content_type and "pdf" in content_type.lower()):
        reader = PdfReader(BytesIO(file_content))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()

    if ext in {"txt", "csv"}:
        return file_content.decode("utf-8", errors="ignore").strip()

    if ext == "docx" or (content_type and "word" in content_type.lower()):
        doc = Document(BytesIO(file_content))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs).strip()

    return ""


def build_vector_chunks_from_parsed(parsed_resume: dict) -> list[dict]:
    """Build Weaviate-ready chunks from parsed resume payload (including LLM-reviewed chunks)."""
    chunks = parsed_resume.get("chunks", []) if isinstance(parsed_resume, dict) else []
    vector_chunks: list[dict] = []

    for idx, chunk in enumerate(chunks):
        text_value = str(chunk.get("text", "")).strip()
        if not text_value:
            continue

        vector_chunks.append(
            {
                "chunk_id": int(chunk.get("chunk_id", idx)),
                "text": text_value,
                "metadata": {
                    "category": chunk.get("category", "other"),
                    "sub_category": chunk.get("sub_category", "general"),
                    "section_heading": chunk.get("section_heading"),
                    "entities": chunk.get("entities", {}),
                    "confidence": chunk.get("confidence", 0.0),
                    "mapped_fields": chunk.get("mapped_fields", []),
                    "needs_review": chunk.get("needs_review", False),
                    "review_reason": chunk.get("review_reason"),
                },
            }
        )

    return vector_chunks


@upload_router.post("/upload")
async def upload_file(file: UploadFile = FastAPIFile(...), token: str = Depends(oath2_schema)):
    """Upload a file and store metadata in MongoDB"""
    try:
        # Get user from token
        user_email = get_user_from_token(token)
        user_data = db["users"].find_one({"email": user_email})
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        if file_size == 0:
            raise HTTPException(status_code=400, detail="Empty file is not allowed")

        cloudinary_resource_type = resolve_cloudinary_resource_type(file.filename or "", file.content_type)
        cloudinary_folder = get_cloudinary_folder(file.filename or "", file.content_type)
        cloudinary_public_id = f"{uuid4()}"

        # Upload file bytes to Cloudinary and persist that URL as file_path
        cloudinary_result = cloudinary.uploader.upload(
            file_content,
            resource_type=cloudinary_resource_type,
            folder=cloudinary_folder,
            public_id=cloudinary_public_id,
            filename_override=file.filename,
            use_filename=True,
            unique_filename=False,
            overwrite=False,
        )
        cloudinary_url = cloudinary_result.get("secure_url")

        if not cloudinary_url:
            raise HTTPException(status_code=500, detail="Cloudinary upload failed: missing secure_url")
        
        extracted_text = extract_text_from_file(file_content, file.filename or "", file.content_type)

        # Create file metadata
        file_doc = {
            "user_id": str(user_data["_id"]),
            "filename": file.filename,
            "file_type": file.filename.split(".")[-1].upper() if "." in file.filename else "FILE",
            "file_size": file_size,
            "upload_date": datetime.now(timezone.utc),
            "file_path": cloudinary_url,
            "status": "uploaded",
            "extracted_text": extracted_text or None,
            "extracted_fields": {},
            "ingest_status": "pending",
            "chunk_count": 0,
            "ingest_error": None,
            "metadata": {
                "content_type": file.content_type,
                "cloudinary_public_id": cloudinary_result.get("public_id"),
                "cloudinary_resource_type": cloudinary_result.get("resource_type"),
                "cloudinary_format": cloudinary_result.get("format"),
            }
        }
        
        # Save to MongoDB first, then index in Weaviate
        result = files_collection.insert_one(file_doc)

        semantic_stored = False
        semantic_chunk_count = 0
        if extracted_text:
            try:
                extracted_fields = parse_resume_text(extracted_text)
                extracted_fields, llm_used, llm_note = review_needs_review_chunks(extracted_fields)
                chunks = build_vector_chunks_from_parsed(extracted_fields)
                ingest_result = ingest_semantic_chunks(
                    file_id=str(result.inserted_id),
                    file_name=file.filename or "",
                    chunks=chunks,
                )
                semantic_chunk_count = ingest_result.get("chunk_count", 0)
                semantic_stored = semantic_chunk_count > 0

                files_collection.update_one(
                    {"_id": result.inserted_id},
                    {
                        "$set": {
                            "extracted_fields": extracted_fields,
                            "ingest_status": "done" if semantic_stored else "pending",
                            "chunk_count": semantic_chunk_count,
                            "ingest_error": None,
                            "metadata.llm_review_used": llm_used,
                            "metadata.llm_review_note": llm_note,
                        }
                    },
                )
            except Exception as ingest_error:
                files_collection.update_one(
                    {"_id": result.inserted_id},
                    {
                        "$set": {
                            "ingest_status": "failed",
                            "ingest_error": str(ingest_error),
                        }
                    },
                )
        
        return {
            "success": True,
            "file_id": str(result.inserted_id),
            "filename": file.filename,
            "file_type": file_doc["file_type"],
            "file_size": file_size,
            "upload_date": file_doc["upload_date"].isoformat(),
            "file_path": file_doc["file_path"],
            "semantic_stored": semantic_stored,
            "chunk_count": semantic_chunk_count,
        }

    except CloudinaryError as e:
        raise HTTPException(status_code=502, detail=f"Cloudinary upload failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Upload failed: {str(e)}")


@upload_router.get("/list")
async def list_files(token: str = Depends(oath2_schema)):
    """Get all files uploaded by current user"""
    try:
        user_email = get_user_from_token(token)
        user_data = db["users"].find_one({"email": user_email})
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's files
        files = files_collection.find({"user_id": str(user_data["_id"])})
        
        return {
            "success": True,
            "files": [
                {
                    "id": str(f["_id"]),
                    "filename": f["filename"],
                    "file_type": f["file_type"],
                    "file_size": f["file_size"],
                    "upload_date": f["upload_date"].isoformat(),
                    "status": f["status"],
                    "ingest_status": f.get("ingest_status", "pending"),
                    "chunk_count": f.get("chunk_count", 0),
                    "ingest_error": f.get("ingest_error"),
                }
                for f in files
            ]
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to list files: {str(e)}")


@upload_router.delete("/{file_id}")
async def delete_file(file_id: str, token: str = Depends(oath2_schema)):
    """Delete a file by ID (only owner can delete)"""
    try:
        from bson import ObjectId
        
        user_email = get_user_from_token(token)
        user_data = db["users"].find_one({"email": user_email})
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Check if file belongs to user
        file_doc = files_collection.find_one({"_id": ObjectId(file_id)})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_doc["user_id"] != str(user_data["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized to delete this file")

        # Best-effort Cloudinary deletion when metadata is present
        cloudinary_public_id = (file_doc.get("metadata") or {}).get("cloudinary_public_id")
        cloudinary_resource_type = (file_doc.get("metadata") or {}).get("cloudinary_resource_type", "auto")
        if cloudinary_public_id:
            try:
                cloudinary.uploader.destroy(
                    cloudinary_public_id,
                    resource_type=cloudinary_resource_type,
                    invalidate=True,
                )
            except Exception:
                # Do not block DB delete if Cloudinary cleanup fails
                pass
        
        # Delete file
        files_collection.delete_one({"_id": ObjectId(file_id)})
        
        return {
            "success": True,
            "message": f"File {file_doc['filename']} deleted successfully"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Delete failed: {str(e)}")


@upload_router.get("/{file_id}")
async def get_file_details(file_id: str, token: str = Depends(oath2_schema)):
    """Get details of a specific file"""
    try:
        from bson import ObjectId
        
        user_email = get_user_from_token(token)
        user_data = db["users"].find_one({"email": user_email})
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")
        
        file_doc = files_collection.find_one({"_id": ObjectId(file_id)})
        
        if not file_doc:
            raise HTTPException(status_code=404, detail="File not found")
        
        if file_doc["user_id"] != str(user_data["_id"]):
            raise HTTPException(status_code=403, detail="Not authorized to access this file")
        
        return {
            "success": True,
            "file": {
                "id": str(file_doc["_id"]),
                "filename": file_doc["filename"],
                "file_type": file_doc["file_type"],
                "file_size": file_doc["file_size"],
                "upload_date": file_doc["upload_date"].isoformat(),
                "status": file_doc["status"],
                "extracted_fields": file_doc.get("extracted_fields", {}),
                "ingest_status": file_doc.get("ingest_status", "pending"),
                "chunk_count": file_doc.get("chunk_count", 0),
                "ingest_error": file_doc.get("ingest_error"),
                "llm_review_used": (file_doc.get("metadata") or {}).get("llm_review_used", False),
                "llm_review_note": (file_doc.get("metadata") or {}).get("llm_review_note"),
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get file: {str(e)}")
