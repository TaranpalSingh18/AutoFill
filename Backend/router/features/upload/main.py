from fastapi import APIRouter, UploadFile, File as FastAPIFile, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import os
from datetime import datetime, timezone
from uuid import uuid4
from jose import jwt
import json

from db.database import db
from models.file import File as FileModel, FileResponse
from router.auth.main import get_current_user

upload_router = APIRouter(tags=["files"], prefix="/files")
files_collection = db["files"]

oath2_schema = OAuth2PasswordBearer(tokenUrl="/auth/login")
secret_key = os.getenv("JWT_SECRET_KEY")
algorithm = os.getenv("JWT_ALGO")

def get_user_from_token(token: str = Depends(oath2_schema)):
    """Extract user from JWT token"""
    try:
        payload = jwt.decode(token, secret_key, algorithms=[algorithm])
        email = payload.get("sub")
        return email
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


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
        
        # Create file metadata
        file_doc = {
            "user_id": str(user_data["_id"]),
            "filename": file.filename,
            "file_type": file.filename.split(".")[-1].upper() if "." in file.filename else "FILE",
            "file_size": file_size,
            "upload_date": datetime.now(timezone.utc),
            "file_path": f"/uploads/{user_data['_id']}/{uuid4()}_{file.filename}",
            "status": "uploaded",
            "extracted_text": None,
            "extracted_fields": {},
            "metadata": {"content_type": file.content_type}
        }
        
        # Save to MongoDB
        result = files_collection.insert_one(file_doc)
        
        return {
            "success": True,
            "file_id": str(result.inserted_id),
            "filename": file.filename,
            "file_type": file_doc["file_type"],
            "file_size": file_size,
            "upload_date": file_doc["upload_date"].isoformat()
        }
    
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
                    "status": f["status"]
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
                "extracted_fields": file_doc.get("extracted_fields", {})
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to get file: {str(e)}")
