from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import core_schema
from typing import Optional, Dict, Any, Annotated
from datetime import datetime
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ]),
        ])

    @classmethod
    def validate(cls, v):
        if isinstance(v, ObjectId):
            return v
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __get_pydantic_json_schema__(cls, handler, info):
        return {"type": "string"}


class File(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    filename: str
    file_type: str  # pdf, docx, xlsx, etc.
    file_size: int  # in bytes
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    file_path: str  # local path or S3 key
    status: str = "uploaded"  # uploaded, processing, ready, error
    extracted_text: Optional[str] = None
    extracted_fields: Optional[Dict[str, Any]] = {}
    metadata: Optional[Dict[str, Any]] = {}


class FileResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    filename: str
    file_type: str
    file_size: int
    upload_date: datetime
    status: str
    extracted_fields: Optional[Dict[str, Any]]


class Section(BaseModel):
    file_id: str
    file_name: str
    file_class: str
    chunk_size: int



