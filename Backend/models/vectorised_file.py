from pydantic import BaseModel
from typing import Optional, Annotated

class SearchFileResponse(BaseModel):
    file_id: str
    file_name: str
    chunk_id: int
    text: str
    score: Optional[float] = None
    