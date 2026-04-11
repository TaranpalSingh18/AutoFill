from __future__ import annotations

from fastapi import APIRouter

from .schemas import ExtractRequirementsBody, ExtractRequirementsResponse
from .service import extract_field_requirements


scraper_router = APIRouter(prefix="/scraper", tags=["scraper"])


@scraper_router.post("/extract-requirements", response_model=ExtractRequirementsResponse)
def extract_requirements(body: ExtractRequirementsBody):
    extracted = extract_field_requirements(body)
    return ExtractRequirementsResponse(
        url=body.url,
        title=body.title,
        total_fields=len(body.fields),
        extracted_requirements=extracted,
    )
