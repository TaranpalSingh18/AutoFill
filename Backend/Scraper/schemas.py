from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class ScrapedField(BaseModel):
    tag: str = "input"
    input_type: Optional[str] = None
    name: Optional[str] = None
    id: Optional[str] = None
    label: Optional[str] = None
    placeholder: Optional[str] = None
    aria_label: Optional[str] = None
    section: Optional[str] = None
    required: bool = False
    options: List[str] = Field(default_factory=list)


class ExtractRequirementsBody(BaseModel):
    url: str
    title: Optional[str] = None
    fields: List[ScrapedField] = Field(default_factory=list)


class FieldRequirement(BaseModel):
    field_key: str
    requirement: str
    required: bool
    input_kind: str
    evidence: List[str] = Field(default_factory=list)
    options: List[str] = Field(default_factory=list)


class ExtractRequirementsResponse(BaseModel):
    url: str
    title: Optional[str] = None
    total_fields: int
    extracted_requirements: List[FieldRequirement] = Field(default_factory=list)
