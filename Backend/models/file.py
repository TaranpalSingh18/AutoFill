from pydantic import BaseModel


class File(BaseModel):
    file_id: str
    name: str
    file_length: int


class Section(BaseModel):
    file_id: str
    file_name: str
    file_class: str
    chunk_size: int



