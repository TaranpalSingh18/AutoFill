import json
import os
import re
from typing import Any, Dict, List, Tuple

ALLOWED_CATEGORIES = {
    "personal_info",
    "education",
    "experience",
    "projects",
    "skills",
    "achievements",
    "certifications",
    "thesis",
    "publications",
    "other",
}


def _extract_first_json_object(text: str) -> Dict[str, Any] | None:
    """Parse the first JSON object from an LLM response safely."""
    text = text.strip()

    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except Exception:
            pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except Exception:
        return None


def _clamp_confidence(value: Any) -> float:
    try:
        conf = float(value)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, conf))


def _normalize_chunk_update(candidate: Dict[str, Any], original_chunk: Dict[str, Any]) -> Dict[str, Any]:
    category = str(candidate.get("category", original_chunk.get("category", "other"))).strip().lower()
    if category not in ALLOWED_CATEGORIES:
        category = original_chunk.get("category", "other")

    mapped_fields = candidate.get("mapped_fields", original_chunk.get("mapped_fields", []))
    if not isinstance(mapped_fields, list):
        mapped_fields = original_chunk.get("mapped_fields", [])

    entities = candidate.get("entities", original_chunk.get("entities", {}))
    if not isinstance(entities, dict):
        entities = original_chunk.get("entities", {})

    return {
        "category": category,
        "sub_category": str(candidate.get("sub_category", original_chunk.get("sub_category", "general"))),
        "confidence": _clamp_confidence(candidate.get("confidence", original_chunk.get("confidence", 0.0))),
        "mapped_fields": mapped_fields,
        "entities": entities,
        "needs_review": bool(candidate.get("needs_review", False)),
        "review_reason": candidate.get("review_reason"),
    }


def review_needs_review_chunks(parsed_resume: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, str | None]:
    """
    Run LLM second-pass on uncertain chunks.

    Returns: (updated_resume, llm_used, llm_note)
    """
    chunks = parsed_resume.get("chunks", [])
    if not isinstance(chunks, list) or not chunks:
        return parsed_resume, False, "No chunks available for LLM review"

    review_indices = [idx for idx, chunk in enumerate(chunks) if chunk.get("needs_review")]
    if not review_indices:
        return parsed_resume, False, "No low-confidence chunks to review"

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return parsed_resume, False, "GROQ_API_KEY is not configured"

    try:
        from langchain_groq import ChatGroq
    except Exception:
        return parsed_resume, False, "langchain-groq is not available"

    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    llm = ChatGroq(api_key=api_key, model=model_name, temperature=0)

    category_list = sorted(ALLOWED_CATEGORIES)
    system_prompt = (
        "You are a resume chunk evaluator. Reclassify ambiguous resume chunks for autofill mapping. "
        "Return strict JSON only."
    )

    reviewed = 0
    for idx in review_indices:
        chunk = chunks[idx]
        user_prompt = {
            "task": "Re-evaluate this resume chunk and improve mapping only if needed.",
            "allowed_categories": category_list,
            "chunk": {
                "text": chunk.get("text", ""),
                "section_heading": chunk.get("section_heading"),
                "current_category": chunk.get("category"),
                "current_sub_category": chunk.get("sub_category"),
                "current_confidence": chunk.get("confidence"),
                "current_entities": chunk.get("entities", {}),
                "current_mapped_fields": chunk.get("mapped_fields", []),
                "current_review_reason": chunk.get("review_reason"),
            },
            "required_output_json_schema": {
                "category": "one of allowed_categories",
                "sub_category": "short string",
                "confidence": "float between 0 and 1",
                "mapped_fields": ["list of mapped field names"],
                "entities": {"key": "value"},
                "needs_review": "boolean",
                "review_reason": "string or null",
            },
            "rules": [
                "Do not hallucinate missing facts.",
                "If uncertain, keep needs_review true.",
                "Prefer conservative extraction.",
            ],
        }

        try:
            response = llm.invoke([
                ("system", system_prompt),
                ("human", json.dumps(user_prompt, ensure_ascii=True)),
            ])
            content = response.content if hasattr(response, "content") else str(response)
            parsed = _extract_first_json_object(content)
            if not parsed:
                continue

            updated = _normalize_chunk_update(parsed, chunk)
            chunks[idx].update(updated)
            reviewed += 1
        except Exception:
            # Keep original chunk if LLM fails on any item.
            continue

    parsed_resume["chunks"] = chunks
    if reviewed == 0:
        return parsed_resume, False, "LLM review failed for all low-confidence chunks"

    return parsed_resume, True, f"LLM reviewed {reviewed} chunk(s)"
