from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Category = Literal[
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
]

CATEGORIES: list[Category] = [
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
]


SECTION_CATEGORY_MAP: dict[str, Category] = {
    "personal": "personal_info",
    "contact": "personal_info",
    "profile": "personal_info",
    "summary": "personal_info",
    "about": "personal_info",
    "education": "education",
    "academic": "education",
    "experience": "experience",
    "employment": "experience",
    "work": "experience",
    "internship": "experience",
    "project": "projects",
    "projects": "projects",
    "skill": "skills",
    "skills": "skills",
    "tech": "skills",
    "achievement": "achievements",
    "achievements": "achievements",
    "award": "achievements",
    "certification": "certifications",
    "certifications": "certifications",
    "certificate": "certifications",
    "thesis": "thesis",
    "publication": "publications",
    "publications": "publications",
    "research": "publications",
}


EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s-]?)?(?:\(?\d{2,4}\)?[\s-]?)\d{3,4}[\s-]?\d{3,4}")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/[^\s|,]+", re.IGNORECASE)
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[^\s|,]+", re.IGNORECASE)
URL_RE = re.compile(r"(?:https?://)?(?:www\.)?[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?", re.IGNORECASE)
YEAR_RE = re.compile(r"\b(19|20)\d{2}\b")
DATE_RANGE_RE = re.compile(
    r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4})\s*[-\u2013]\s*((?:Present|Current|Now)|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}|\d{4})",
    re.IGNORECASE,
)


CATEGORY_HINTS: dict[Category, tuple[str, ...]] = {
    "personal_info": ("email", "phone", "linkedin", "github", "portfolio", "contact"),
    "education": ("university", "college", "b.tech", "bachelor", "master", "gpa", "cgpa"),
    "experience": ("experience", "engineer", "developer", "intern", "company", "worked"),
    "projects": ("project", "built", "developed", "implemented", "repository", "github"),
    "skills": ("skills", "tools", "languages", "frameworks", "technologies"),
    "achievements": ("achievement", "award", "winner", "rank", "recognition"),
    "certifications": ("certification", "certificate", "issued", "coursera", "udemy"),
    "thesis": ("thesis", "dissertation", "research work", "advisor", "supervisor", "guide", "abstract", "capstone"),
    "publications": ("publication", "journal", "conference", "paper", "doi"),
    "other": (),
}


FIELD_MAPPING_BY_CATEGORY: dict[Category, tuple[str, ...]] = {
    "personal_info": ("name", "email", "phone", "linkedin", "github", "portfolio"),
    "education": ("institution", "degree", "field", "start_year", "end_year"),
    "experience": ("company", "role", "duration", "location", "key_points"),
    "projects": ("project_name", "tech_stack", "description"),
    "skills": ("skills",),
    "achievements": ("title", "issuer", "year"),
    "certifications": ("title", "issuer", "year"),
    "thesis": ("title", "issuer", "year"),
    "publications": ("title", "issuer", "year"),
    "other": (),
}


class PersonalInfoEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None


class ExperienceEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    company: Optional[str] = None
    role: Optional[str] = None
    duration: Optional[str] = None
    location: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)


class EducationEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    institution: Optional[str] = None
    degree: Optional[str] = None
    field: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None


class ProjectEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_name: Optional[str] = None
    tech_stack: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class SkillsEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    skills: Dict[str, List[str]] = Field(default_factory=dict)


class AchievementOrCertificationEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class ThesisEntity(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: Optional[str] = None
    issuer: Optional[str] = None
    year: Optional[str] = None


class SemanticChunk(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunk_id: int
    category: Category
    sub_category: str
    text: str
    section_heading: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)
    confidence: float = 0.0
    category_scores: Dict[str, float] = Field(default_factory=dict)
    mapped_fields: List[str] = Field(default_factory=list)
    needs_review: bool = False
    review_reason: Optional[str] = None


class StructuredResume(BaseModel):
    model_config = ConfigDict(extra="ignore")

    chunks: List[SemanticChunk]


@dataclass
class _Section:
    heading: str
    lines: list[str]


class ResumeSemanticChunker:
    """Rule-based semantic chunker for resume text to strict JSON-friendly chunks."""

    def parse(self, text: str) -> StructuredResume:
        cleaned_lines = self._normalize_lines(text)
        sections = self._detect_sections(cleaned_lines)

        chunks: list[SemanticChunk] = []
        chunk_id = 0
        for section in sections:
            section_category = self._section_to_category(section.heading, section.lines)
            section_chunks = self._chunk_section(section, section_category)
            for raw_chunk in section_chunks:
                category, confidence, category_scores = self._classify_chunk(raw_chunk, section_category)
                entities = self._extract_entities(raw_chunk, category)
                sub_category = self._infer_sub_category(raw_chunk, category)
                mapped_fields = self._resolve_mapped_fields(category, entities)
                needs_review, review_reason = self._review_decision(
                    category=category,
                    confidence=confidence,
                    mapped_fields=mapped_fields,
                    entities=entities,
                )
                chunks.append(
                    SemanticChunk(
                        chunk_id=chunk_id,
                        category=category,
                        sub_category=sub_category,
                        text=raw_chunk,
                        section_heading=section.heading,
                        entities=entities,
                        confidence=confidence,
                        category_scores=category_scores,
                        mapped_fields=mapped_fields,
                        needs_review=needs_review,
                        review_reason=review_reason,
                    )
                )
                chunk_id += 1

        if not chunks and cleaned_lines:
            fallback_text = " ".join(cleaned_lines)
            chunks.append(
                SemanticChunk(
                    chunk_id=0,
                    category="other",
                    sub_category="general",
                    text=fallback_text,
                    section_heading=None,
                    entities={},
                    confidence=0.0,
                    category_scores={"other": 1.0},
                    mapped_fields=[],
                    needs_review=True,
                    review_reason="Could not infer structured section from text.",
                )
            )

        return StructuredResume(chunks=chunks)

    def parse_to_dict(self, text: str) -> Dict[str, Any]:
        return self.parse(text).model_dump(exclude_none=True)

    def chunks_for_vector_db(self, text: str) -> List[Dict[str, Any]]:
        """Create records ready for vector DB ingestion with semantic metadata."""
        parsed = self.parse(text)
        payload: list[dict[str, Any]] = []
        for chunk in parsed.chunks:
            payload.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "text": chunk.text,
                    "metadata": {
                        "category": chunk.category,
                        "sub_category": chunk.sub_category,
                        "section_heading": chunk.section_heading,
                        "entities": chunk.entities,
                        "confidence": chunk.confidence,
                        "mapped_fields": chunk.mapped_fields,
                        "needs_review": chunk.needs_review,
                        "review_reason": chunk.review_reason,
                    },
                }
            )
        return payload

    def _classify_chunk(self, chunk_text: str, section_category: Category) -> tuple[Category, float, dict[str, float]]:
        text_low = chunk_text.lower()
        scores: dict[Category, float] = {category: 0.0 for category in CATEGORIES}

        for category, hints in CATEGORY_HINTS.items():
            score = 0.0
            for hint in hints:
                if hint in text_low:
                    score += 0.2
            scores[category] = score

        # Structure cues
        if EMAIL_RE.search(chunk_text) or PHONE_RE.search(chunk_text):
            scores["personal_info"] += 0.35
        if DATE_RANGE_RE.search(chunk_text):
            scores["experience"] += 0.2
            scores["education"] += 0.1
        if YEAR_RE.search(chunk_text):
            scores["education"] += 0.1
            scores["certifications"] += 0.1

        # Section prior
        scores[section_category] += 0.25

        # Thesis content overlaps with education/projects, so give section-level thesis a stronger prior.
        if section_category == "thesis":
            scores["thesis"] += 0.35

        # Keep other as fallback, but prefer specific classes when evidence exists.
        if max(scores.values()) <= 0.05:
            scores["other"] = 1.0
        else:
            scores["other"] += 0.02

        sorted_items = sorted(scores.items(), key=lambda item: item[1], reverse=True)
        best_category = sorted_items[0][0]
        best_score = sorted_items[0][1]
        second_score = sorted_items[1][1] if len(sorted_items) > 1 else 0.0

        normalized_best = min(1.0, max(0.0, best_score))
        confidence = round(max(0.0, normalized_best - second_score + 0.4), 3)
        confidence = min(1.0, confidence)

        top_scores = {k: round(v, 3) for k, v in sorted_items[:3] if v > 0}
        if best_category not in top_scores:
            top_scores[best_category] = round(best_score, 3)

        return best_category, confidence, top_scores

    def _resolve_mapped_fields(self, category: Category, entities: dict[str, Any]) -> list[str]:
        allowed_fields = set(FIELD_MAPPING_BY_CATEGORY.get(category, ()))
        mapped = [key for key in entities.keys() if key in allowed_fields and entities.get(key) not in (None, "", [], {})]
        if not mapped:
            return list(allowed_fields)
        return mapped

    def _review_decision(
        self,
        category: Category,
        confidence: float,
        mapped_fields: list[str],
        entities: dict[str, Any],
    ) -> tuple[bool, Optional[str]]:
        if category == "other":
            return True, "Chunk could not be mapped to a known resume category."
        if confidence < 0.55:
            return True, f"Low classification confidence ({confidence:.2f})."
        if not entities:
            return True, "No entities extracted from this chunk."
        if not mapped_fields:
            return True, "No target autofill fields were mapped from extracted entities."
        return False, None

    def _normalize_lines(self, text: str) -> list[str]:
        lines = [line.strip() for line in text.splitlines()]
        lines = [re.sub(r"\s+", " ", line) for line in lines]
        return [line for line in lines if line]

    def _detect_sections(self, lines: list[str]) -> list[_Section]:
        if not lines:
            return []

        sections: list[_Section] = []
        current_heading = "general"
        current_lines: list[str] = []

        for line in lines:
            if self._is_heading(line):
                if current_lines:
                    sections.append(_Section(heading=current_heading, lines=current_lines))
                current_heading = line
                current_lines = []
            else:
                current_lines.append(line)

        if current_lines:
            sections.append(_Section(heading=current_heading, lines=current_lines))

        return sections

    def _is_heading(self, line: str) -> bool:
        normalized = line.lower().strip(" :")
        if normalized in SECTION_CATEGORY_MAP:
            return True

        words = normalized.split()
        if 0 < len(words) <= 5 and line == line.upper() and any(k in normalized for k in SECTION_CATEGORY_MAP):
            return True

        common_heading_tokens = {
            "education",
            "experience",
            "projects",
            "skills",
            "achievements",
            "certifications",
            "publications",
            "thesis",
            "summary",
            "profile",
            "contact",
        }
        return len(words) <= 4 and all(token in common_heading_tokens for token in words if token.isalpha())

    def _section_to_category(self, heading: str, lines: list[str]) -> Category:
        normalized = heading.lower().strip(" :")
        for key, value in SECTION_CATEGORY_MAP.items():
            if key in normalized:
                return value

        sample = " ".join(lines[:5]).lower()
        if any(keyword in sample for keyword in ("university", "b.tech", "bachelor", "master", "gpa")):
            return "education"
        if any(keyword in sample for keyword in ("intern", "engineer", "developer", "worked", "company")):
            return "experience"
        if any(keyword in sample for keyword in ("python", "java", "react", "docker", "skills", "tools")):
            return "skills"
        if any(keyword in sample for keyword in ("built", "developed", "project", "github")):
            return "projects"
        if any(keyword in sample for keyword in ("thesis", "dissertation", "advisor", "supervisor", "abstract", "capstone")):
            return "thesis"

        return "other"

    def _chunk_section(self, section: _Section, category: Category) -> list[str]:
        if not section.lines:
            return []

        if category in {"skills", "personal_info"}:
            return [" | ".join(section.lines)]

        chunks: list[list[str]] = []
        current: list[str] = []

        for line in section.lines:
            new_unit = self._looks_like_new_item(line, category)
            if new_unit and current:
                chunks.append(current)
                current = [line]
            else:
                current.append(line)

        if current:
            chunks.append(current)

        return [" ".join(lines).strip() for lines in chunks if lines]

    def _looks_like_new_item(self, line: str, category: Category) -> bool:
        bullet = line.startswith(("-", "*", "•"))
        years = len(YEAR_RE.findall(line))
        has_date_range = bool(DATE_RANGE_RE.search(line))

        if category in {"experience", "education", "projects"}:
            if has_date_range:
                return True
            if years >= 1 and not bullet:
                return True
            if line.istitle() and len(line.split()) <= 10:
                return True

        if category in {"achievements", "certifications", "publications", "thesis"}:
            return bullet or years >= 1

        return False

    def _extract_entities(self, chunk_text: str, category: Category) -> dict[str, Any]:
        if category == "personal_info":
            return self._extract_personal_info(chunk_text).model_dump(exclude_none=True)
        if category == "experience":
            return self._extract_experience(chunk_text).model_dump(exclude_none=True)
        if category == "education":
            return self._extract_education(chunk_text).model_dump(exclude_none=True)
        if category == "projects":
            return self._extract_project(chunk_text).model_dump(exclude_none=True)
        if category == "skills":
            return self._extract_skills(chunk_text).model_dump(exclude_none=True)
        if category == "thesis":
            return self._extract_thesis(chunk_text).model_dump(exclude_none=True)
        if category in {"achievements", "certifications", "publications"}:
            return self._extract_achievement_or_certification(chunk_text).model_dump(exclude_none=True)
        return {}

    def _extract_thesis(self, text: str) -> ThesisEntity:
        year_values = re.findall(r"\b(?:19|20)\d{2}\b", text)
        year = year_values[0] if year_values else None

        issuer = None
        advisor_match = re.search(r"(?:advisor|supervisor|guide)\s*[:\-]\s*([^|,]+)", text, flags=re.IGNORECASE)
        if advisor_match:
            issuer = advisor_match.group(1).strip()

        title = None
        title_match = re.search(r"(?:thesis|dissertation|capstone)\s*(?:title)?\s*[:\-]\s*([^|]+)", text, flags=re.IGNORECASE)
        if title_match:
            title = title_match.group(1).strip()
        else:
            parts = [p.strip() for p in re.split(r"\||,", text) if p.strip()]
            if parts:
                title = parts[0]

        return ThesisEntity(title=title, issuer=issuer, year=year)

    def _extract_personal_info(self, text: str) -> PersonalInfoEntity:
        emails = EMAIL_RE.findall(text)
        phones = PHONE_RE.findall(text)
        linkedin = self._first_match(LINKEDIN_RE, text)
        github = self._first_match(GITHUB_RE, text)

        all_urls = URL_RE.findall(text)
        portfolio = None
        for url in all_urls:
            low = url.lower()
            if "linkedin.com" in low or "github.com" in low:
                continue
            portfolio = url
            break

        name = self._infer_name_from_header(text)

        return PersonalInfoEntity(
            name=name,
            email=emails[0] if emails else None,
            phone=phones[0] if phones else None,
            linkedin=linkedin,
            github=github,
            portfolio=portfolio,
        )

    def _extract_experience(self, text: str) -> ExperienceEntity:
        lines = self._split_for_entities(text)
        role, company = self._infer_role_company(lines[0] if lines else text)
        duration = self._first_match(DATE_RANGE_RE, text, group_join=True)
        location = self._infer_location(text)
        key_points = [line.lstrip("-*• ").strip() for line in lines[1:] if line.strip()]

        return ExperienceEntity(
            company=company,
            role=role,
            duration=duration,
            location=location,
            key_points=key_points,
        )

    def _extract_education(self, text: str) -> EducationEntity:
        lines = self._split_for_entities(text)
        head = lines[0] if lines else text
        institution = self._infer_institution(head)
        degree = self._infer_degree(text)
        field = self._infer_field(text)
        years = YEAR_RE.findall(text)
        year_values = re.findall(r"\b(?:19|20)\d{2}\b", text)

        start_year = year_values[0] if year_values else None
        end_year = year_values[1] if len(year_values) > 1 else None

        return EducationEntity(
            institution=institution,
            degree=degree,
            field=field,
            start_year=start_year,
            end_year=end_year,
        )

    def _extract_project(self, text: str) -> ProjectEntity:
        lines = self._split_for_entities(text)
        project_name = self._infer_project_name(lines[0] if lines else text)
        tech_stack = self._extract_tech_stack(text)
        description = " ".join(lines[1:]).strip() if len(lines) > 1 else text

        return ProjectEntity(
            project_name=project_name,
            tech_stack=tech_stack,
            description=description,
        )

    def _extract_skills(self, text: str) -> SkillsEntity:
        grouped: dict[str, list[str]] = {}

        parts = re.split(r"[|\n]", text)
        for part in parts:
            candidate = part.strip()
            if not candidate:
                continue

            if ":" in candidate:
                group, values = candidate.split(":", 1)
                key = group.strip().lower().replace(" ", "_")
                grouped[key] = [v.strip() for v in re.split(r",|/", values) if v.strip()]
            else:
                grouped.setdefault("general", []).extend(
                    [v.strip() for v in re.split(r",|/", candidate) if v.strip()]
                )

        deduped = {k: self._dedupe_keep_order(v) for k, v in grouped.items()}
        return SkillsEntity(skills=deduped)

    def _extract_achievement_or_certification(self, text: str) -> AchievementOrCertificationEntity:
        year_values = re.findall(r"\b(?:19|20)\d{2}\b", text)
        year = year_values[0] if year_values else None

        parts = [p.strip() for p in re.split(r"-|\||,", text) if p.strip()]
        title = parts[0] if parts else text
        issuer = parts[1] if len(parts) > 1 else None

        return AchievementOrCertificationEntity(title=title, issuer=issuer, year=year)

    def _infer_sub_category(self, chunk_text: str, category: Category) -> str:
        if category == "experience":
            role, _company = self._infer_role_company(chunk_text)
            return role or "work_experience"
        if category == "education":
            degree = self._infer_degree(chunk_text)
            return degree or "degree"
        if category == "projects":
            return self._infer_project_name(chunk_text) or "project"
        if category == "skills":
            return "skill_group"
        if category == "personal_info":
            return "contact_profile"
        if category == "certifications":
            return "professional_certification"
        if category == "achievements":
            return "award_or_achievement"
        if category == "publications":
            return "research_publication"
        if category == "thesis":
            return "thesis_work"
        return "general"

    def _split_for_entities(self, text: str) -> list[str]:
        return [part.strip() for part in re.split(r"\s{2,}|\n|\|", text) if part.strip()]

    def _infer_name_from_header(self, text: str) -> Optional[str]:
        first = text.split("|")[0].strip()
        first = re.sub(r"\s+", " ", first)
        words = first.split()
        if 2 <= len(words) <= 5 and all(word and word[0].isalpha() for word in words):
            return first
        return None

    def _first_match(self, pattern: re.Pattern[str], text: str, group_join: bool = False) -> Optional[str]:
        match = pattern.search(text)
        if not match:
            return None
        if group_join and match.groups():
            return " - ".join(g for g in match.groups() if g)
        return match.group(0)

    def _infer_role_company(self, text: str) -> tuple[Optional[str], Optional[str]]:
        # Common formats: "Role at Company", "Role | Company", "Company - Role"
        text = text.strip().lstrip("-*• ")

        if " at " in text.lower():
            parts = re.split(r"\bat\b", text, flags=re.IGNORECASE, maxsplit=1)
            if len(parts) == 2:
                return parts[0].strip(), parts[1].strip()

        if "|" in text:
            parts = [p.strip() for p in text.split("|", 1)]
            if len(parts) == 2:
                return parts[0], parts[1]

        if " - " in text:
            parts = [p.strip() for p in text.split(" - ", 1)]
            if len(parts) == 2:
                # Heuristic: if left side has org-like suffix, treat as company first
                left = parts[0]
                if any(tok in left.lower() for tok in ["inc", "llc", "ltd", "technologies", "systems", "corp"]):
                    return parts[1], left
                return parts[0], parts[1]

        return None, None

    def _infer_location(self, text: str) -> Optional[str]:
        location_markers = ["remote", "onsite", "hybrid"]
        low = text.lower()
        for marker in location_markers:
            if marker in low:
                return marker.title()

        # Fallback: city-like token around commas
        parts = [p.strip() for p in text.split(",")]
        for part in parts:
            if 1 <= len(part.split()) <= 3 and not YEAR_RE.search(part):
                if any(ch.isalpha() for ch in part):
                    return part
        return None

    def _infer_institution(self, text: str) -> Optional[str]:
        text_low = text.lower()
        institution_tokens = ["university", "college", "institute", "school"]
        if any(tok in text_low for tok in institution_tokens):
            return text
        return None

    def _infer_degree(self, text: str) -> Optional[str]:
        degree_patterns = [
            r"\bB\.?Tech\b",
            r"\bM\.?Tech\b",
            r"\bB\.?E\b",
            r"\bM\.?E\b",
            r"\bBachelor(?:'s)?\b",
            r"\bMaster(?:'s)?\b",
            r"\bPh\.?D\b",
            r"\bMBA\b",
        ]
        for pattern in degree_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(0)
        return None

    def _infer_field(self, text: str) -> Optional[str]:
        field_patterns = [
            r"in ([A-Za-z &]+)",
            r"\bComputer Science\b",
            r"\bInformation Technology\b",
            r"\bElectrical(?: and Electronics)? Engineering\b",
            r"\bMechanical Engineering\b",
        ]
        for pattern in field_patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return match.group(1) if match.lastindex else match.group(0)
        return None

    def _infer_project_name(self, text: str) -> Optional[str]:
        head = text.strip().split("|")[0].strip()
        head = head.split(" - ")[0].strip()
        if 2 <= len(head) <= 120:
            return head
        return None

    def _extract_tech_stack(self, text: str) -> list[str]:
        known = [
            "python",
            "java",
            "c++",
            "javascript",
            "typescript",
            "react",
            "node",
            "fastapi",
            "django",
            "flask",
            "mongodb",
            "mysql",
            "postgresql",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "langchain",
            "weaviate",
            "pytorch",
            "tensorflow",
            "scikit-learn",
        ]
        low = text.lower()
        found = [item for item in known if item in low]
        return self._dedupe_keep_order(found)

    def _dedupe_keep_order(self, values: Iterable[str]) -> list[str]:
        seen: set[str] = set()
        out: list[str] = []
        for value in values:
            key = value.lower().strip()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(value.strip())
        return out


def parse_resume_text(text: str) -> Dict[str, Any]:
    """Convenience function returning strict JSON-serializable dict."""
    return ResumeSemanticChunker().parse_to_dict(text)


def vector_ready_chunks(text: str) -> List[Dict[str, Any]]:
    """Convenience function for vector DB ingestion payload."""
    return ResumeSemanticChunker().chunks_for_vector_db(text)
