from pydantic import BaseModel, Field, ConfigDict
from pydantic_core import core_schema
from typing import Optional, List, Annotated
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


class VectorisedFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    file_id: PyObjectId
    chunk_id: int
    text: str
    embedding: List[float]  # List of floats from embedding model
    metadata: Optional[dict] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SearchFileResponse(BaseModel):
    file_id: str
    file_name: str
    chunk_id: int
    text: str
    score: Optional[float] = None


class Template(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    name: str
    description: Optional[str] = None
    file_id: PyObjectId
    fields: List[dict]  # [{name: str, type: str, required: bool, default: Any}]
    field_mapping: dict  # {source_field: target_field}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Job(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    user_id: PyObjectId
    file_id: PyObjectId
    template_id: Optional[PyObjectId] = None
    user_data: dict  # {field_name: value} - data to fill
    status: str = "pending"  # pending, processing, completed, failed
    result_file_path: Optional[str] = None
    error_message: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    metadata: Optional[dict] = {}


class JobResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)
    
    id: Optional[PyObjectId] = Field(alias="_id")
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    error_message: Optional[str]
    