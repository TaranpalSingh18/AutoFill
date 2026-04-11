from __future__ import annotations

import re
from typing import List

from .schemas import ExtractRequirementsBody, FieldRequirement, ScrapedField


def _clean_text(value: str | None) -> str:
    if not value:
        return ""
    return re.sub(r"\s+", " ", value).strip()


def _slug(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_") or "field"


def _best_label(field: ScrapedField) -> str:
    for candidate in [field.label, field.aria_label, field.placeholder, field.name, field.id]:
        cleaned = _clean_text(candidate)
        if cleaned:
            return cleaned
    return "Unnamed field"


def _resolve_kind(field: ScrapedField) -> str:
    tag = (field.tag or "input").lower()
    input_type = (field.input_type or "").lower()

    if tag == "select":
        return "select"
    if tag == "textarea":
        return "textarea"
    if input_type in {"email", "tel", "number", "date", "url", "password", "checkbox", "radio"}:
        return input_type
    return "text"


def _build_requirement(field: ScrapedField) -> FieldRequirement:
    label = _best_label(field)
    kind = _resolve_kind(field)

    requirement_chunks: List[str] = [label]
    if field.section:
        requirement_chunks.append(f"section: {field.section}")
    requirement_chunks.append(f"type: {kind}")
    if field.required:
        requirement_chunks.append("required")
    if field.options:
        requirement_chunks.append("choose from allowed options")

    evidence = []
    for item in [field.label, field.placeholder, field.aria_label, field.name, field.id, field.section]:
        cleaned = _clean_text(item)
        if cleaned:
            evidence.append(cleaned)

    key_seed = field.name or field.id or label
    field_key = _slug(key_seed)

    return FieldRequirement(
        field_key=field_key,
        requirement=" | ".join(requirement_chunks),
        required=field.required,
        input_kind=kind,
        evidence=evidence,
        options=[_clean_text(option) for option in field.options if _clean_text(option)],
    )


def extract_field_requirements(payload: ExtractRequirementsBody) -> list[FieldRequirement]:
    requirements: list[FieldRequirement] = []
    seen_keys: set[str] = set()

    for field in payload.fields:
        result = _build_requirement(field)

        original_key = result.field_key
        suffix = 2
        while result.field_key in seen_keys:
            result.field_key = f"{original_key}_{suffix}"
            suffix += 1

        seen_keys.add(result.field_key)
        requirements.append(result)

    return requirements
