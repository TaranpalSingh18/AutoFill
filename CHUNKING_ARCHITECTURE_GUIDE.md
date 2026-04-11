# AutoFill Backend Architecture: AI Model & Chunking Pipeline

## 📋 Executive Summary

Your backend uses a **hybrid chunking strategy** that combines:
- **Rule-based semantic chunking** (primary strategy)
- **LLM-powered review mechanism** (secondary validation)
- **Vector embeddings** (for semantic search)

This document explains the exact flow from file upload to stored vector chunks.

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     FILE UPLOAD ENDPOINT                     │
│            (FastAPI: /files/upload)                          │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼  
┌─────────────────────────────────────────────────────────────┐
│         1. TEXT EXTRACTION LAYER                             │
│   - PDFs → parse with PyPDF                                  │
│   - DOCX → parse with python-docx                            │
│   - TXT/CSV → decode UTF-8                                   │
│   Output: Raw Resume Text String                             │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         2. SEMANTIC CHUNKING (Rule-Based)                    │
│   ResumeSemanticChunker.parse()                              │
│   - Line normalization                                        │
│   - Section detection (headings)                              │
│   - Content chunking per section                              │
│   Output: SemanticChunk[] with metadata                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         3. ENTITY EXTRACTION & CLASSIFICATION                │
│   For each chunk:                                             │
│   - Extract structured entities                              │
│   - Classify category (10 categories)                         │
│   - Calculate confidence score                                │
│   - Determine if needs review                                 │
│   Output: Enriched SemanticChunk                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
        ▼                             ▼
    High Confidence           Low Confidence
    (Confidence ≥ 0.55)       (Confidence < 0.55)
        │                             │
        │                             ▼
        │              ┌──────────────────────────────┐
        │              │  4. LLM REVIEW (GROQ)        │
        │              │  - Re-classify chunk         │
        │              │  - Improve entity extraction │
        │              │  - Update confidence         │
        │              └──────────────┬───────────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         5. VECTOR EMBEDDING & STORAGE                        │
│   - Generate embeddings (all-MiniLM-L6-v2)                   │
│   - Store in Weaviate (vector DB)                            │
│   - Metadata preserved for retrieval                          │
│   Output: Searchable vector chunks                            │
└─────────────────────────────────────────────────────────────┘

                       │
                       ▼
            ┌──────────────────────────┐
            │   SEARCH/RETRIEVAL READY │
            │   (Semantic Search)      │
            └──────────────────────────┘
```

---

## 🔄 Detailed Pipeline Steps

### **Step 1: Text Extraction**
**File:** `router/features/upload/main.py` → `extract_text_from_file()`

```python
# Input: Binary file content + filename
# Process:
- PDF: Extract all pages using PyPDF → join with newlines
- DOCX: Extract paragraphs using python-docx → join with newlines  
- TXT/CSV: Decode UTF-8 directly
# Output: String of resume text
```

**Why this matters:** Standardizes all input formats to raw text before chunking.

---

### **Step 2: Semantic Chunking (Rule-Based)**
**File:** `Chunking/semantic_chunking.py` → `ResumeSemanticChunker.parse()`

#### **Sub-Step 2.1: Line Normalization**
```
Input:  "    John    Smith    \n\n   Email:   john@test.com   "
        ↓ Remove leading/trailing whitespace per line
        ↓ Normalize multiple spaces to single space
        ↓ Filter empty lines
Output: ["John Smith", "Email: john@test.com"]
```

#### **Sub-Step 2.2: Section Detection (Heading Recognition)**
**Algorithm:** Identify section headings using:
- Dictionary lookup: "personal", "education", "experience" → known section
- Pattern matching: ALL CAPS lines with ≤5 words + heading keywords
- Heuristic: ≤4 words, all from [education, experience, projects, skills, ...]

**Categories recognized (10 total):**
```
1. personal_info     → Contact details (name, email, phone, links)
2. education        → University/degree information
3. experience       → Job roles and employment history
4. projects         → Portfolio/projects section
5. skills           → Technologies and tools
6. achievements     → Awards and recognition
7. certifications   → Professional certifications
8. thesis           → Thesis/dissertation work
9. publications     → Research papers/publications
10. other           → Unclassified content
```

**Output:** Detected sections organized as `_Section(heading, lines[])`

---

#### **Sub-Step 2.3: Content Chunking Per Section**

Different strategies per category:

| Category | Strategy |
|----------|----------|
| `skills`, `personal_info` | **Single chunk** - join all lines with `\|` |
| `experience`, `education`, `projects` | **Split on date ranges or year patterns** - each item is dated |
| `achievements`, `certifications`, `publications`, `thesis` | **Split on bullets or years** |

**Example (Experience Section):**
```
Input Lines:
  - "Software Engineer at Google | 2020-2022"
  - "  - Led 5-person team"
  - "  - Shipped ML pipeline"
  - "Data Scientist at Microsoft | 2022-Present"
  - "  - Built recommendation engine"

Chunk Detection Logic:
  Line 1: has DATE_RANGE → start NEW chunk #1
  Line 2-3: no new date → add to chunk #1
  Line 4: has DATE_RANGE → start NEW chunk #2
  Line 5: no new date → add to chunk #2

Output Chunks:
  Chunk 1: "Software Engineer at Google | 2020-2022 Led 5-person team Shipped ML pipeline"
  Chunk 2: "Data Scientist at Microsoft | 2022-Present Built recommendation engine"
```

---

### **Step 3: Entity Extraction & Classification**

For **each chunk**, simultaneously:

#### **3A. Assign Section Category**
Uses section heading + sample text heuristics to assign initial category.

#### **3B. Extract Structured Entities**

| Category | Extracted Fields |
|----------|------------------|
| `personal_info` | name, email, phone, linkedin, github, portfolio |
| `experience` | company, role, duration, location, key_points[] |
| `education` | institution, degree, field, start_year, end_year |
| `projects` | project_name, tech_stack[], description |
| `skills` | skills{group: [tech_list]} |
| `certifications` | title, issuer, year |
| `thesis` | title, advisor/issuer, year |
| `achievements` | title, issuer, year |

**Extraction methods (regex-based):**
```python
# Email: EMAIL_RE pattern → find all → take first
# Phone: PHONE_RE pattern → find all → take first
# Dates: DATE_RANGE_RE, YEAR_RE patterns
# Role parsing: "Role at Company" or "Role | Company" split
# Skills: Split by comma/slash, group by "Type: skill1, skill2"
```

#### **3C. Classification Scoring Algorithm**

Each chunk gets scored across all 10 categories using:

1. **Keyword hints** (0.2 points per hint match)
   - "personal_info" hints: email, phone, linkedin, github, ...
   - "experience" hints: engineer, developer, intern, company, ...
   - etc.

2. **Structural patterns** (context-dependent)
   - Email/Phone found → +0.35 to personal_info
   - Date range found → +0.2 to experience, +0.1 to education
   - Year pattern → +0.1 to education, +0.1 to certifications

3. **Section prior** (strong signal)
   - Section category gets +0.25
   - Thesis section gets +0.35 (overlaps with education/projects)

4. **Fallback logic**
   - If no high signals → "other" gets 1.0
   - Otherwise "other" gets +0.02

5. **Confidence calculation**
   ```
   confidence = max(0.0, min(1.0, best_score - second_score + 0.4))
   ```
   - High separation = high confidence
   - Close scores = low confidence

**Output:** 
- `category`: highest-scoring category
- `confidence`: 0-1 float score
- `category_scores`: top 3 categories with scores

#### **3D. Review Decision**

Mark chunk for LLM review if **ANY** condition true:
```python
if category == "other":
    needs_review = True  # Unclassified entirely
elif confidence < 0.55:
    needs_review = True  # Ambiguous classification
elif not entities:
    needs_review = True  # No data extracted
elif not mapped_fields:
    needs_review = True  # No target autofill fields identified
else:
    needs_review = False  # High-quality, auto-approved
```

---

### **Step 4: LLM Review (Second-Pass Validation)**
**File:** `Chunking/llm_reviewer.py` → `review_needs_review_chunks()`

**Trigger:** Only chunks with `needs_review = True`

**LLM Provider:** Groq (llama-3.3-70b-versatile, temperature=0)

**Process:**
```
1. For EACH flagged chunk:
   - Send chunk text + classification reason to LLM via JSON prompt
   - LLM task: "Re-evaluate this chunk and improve mapping if needed"
   - LLM constraints: 
     * Return strict JSON only
     * Only use allowed categories
     * Be conservative with extraction
     * Keep needs_review=true if still uncertain

2. Parse LLM response:
   - Extract first JSON object from response
   - Validate category is in allowed list
   - Clamp confidence to [0.0, 1.0]
   - Update chunk with LLM's improved classification

3. Fallback:
   - If LLM fails on any chunk → keep original classification
   - Return: (updated_resume, llm_used=true, review_count=N)
```

**Why LLM?**
- Catches edge cases rule-based chunker misses
- Nuanced understanding of resume context
- Can re-weight mapped fields based on intent
- Human fallback for ambiguous chunks

---

### **Step 5: Vector Embedding & Storage**
**File:** `router/features/retrieval/vector_db.py`

#### **5A: Transform to Vector Chunks**
```python
# For each chunk, create:
{
    "chunk_id": 0,
    "text": "Full chunk text",
    "metadata": {
        "category": "experience",
        "sub_category": "Software Engineer",  # role-specific
        "section_heading": "Experience",
        "entities": {"company": "Google", "role": "Engineer", ...},
        "confidence": 0.87,
        "mapped_fields": ["company", "role", "duration"],
        "needs_review": False,
        "review_reason": None
    }
}
```

#### **5B: Generate Embeddings**
**Model:** `sentence-transformers/all-MiniLM-L6-v2`
- 384-dimensional embeddings
- Optimized for semantic similarity
- Fast inference

```python
embeddings = embed_documents([chunk.text for chunk in chunks])
# Returns: list[list[float]] - one 384-dim vector per chunk
```

#### **5C: Store in Weaviate**
**Vector Database:** Weaviate (cloud-hosted)

**Collection schema:**
```
{
  "name": "DocumentChunk",
  "properties": {
    "file_id": TEXT,
    "file_name": TEXT,
    "chunk_id": INT,
    "text": TEXT,
    "category": TEXT,
    "sub_category": TEXT,
    "section_heading": TEXT,
    "embedding": VECTOR[384]  # Auto-indexed
  }
}
```

**Stored record:**
```json
{
  "_id": "uuid-generated",
  "file_id": "MongoDB ObjectId",
  "file_name": "resume.pdf",
  "chunk_id": 0,
  "text": "John Smith | john@example.com | +1-234-567-8900",
  "category": "personal_info",
  "sub_category": "contact_profile",
  "section_heading": "Contact",
  "embedding": [0.45, -0.12, 0.78, ...]  // 384 floats
}
```

---

## 📊 Data Flow: Complete Example

### Input Resume (Simplified):
```
JOHN SMITH
john@test.com | +1-234-567-890 | linkedin.com/in/johnsmith

EDUCATION
Bachelor of Technology in Computer Science
Indian Institute of Technology Delhi
2018-2022 | CGPA: 8.5/10

EXPERIENCE
Software Engineer at Google
2022-Present | Remote
- Led migration of 10M+ records to new database
- Improved query performance by 40%

Data Scientist at Microsoft
2020-2022 | Seattle, WA
- Built recommendation engine serving 100M+ users
- Deployed ML pipeline with 95% accuracy

SKILLS
Languages: Python, Java, C++
Frameworks: React, Django, FastAPI
Databases: PostgreSQL, MongoDB
```

### Processing Through Pipeline:

**Step 2.2 (Section Detection):**
```
Section 1: heading="JOHN SMITH", lines=["JOHN SMITH", "john@test.com | +1-234-567-890 | ..."]
Section 2: heading="EDUCATION", lines=["Bachelor of Technology...", "Indian Institute...", ...]
Section 3: heading="EXPERIENCE", lines=["Software Engineer...", "- Led migration...", ...]
Section 4: heading="SKILLS", lines=["Languages:...", "Frameworks:...", ...]
```

**Step 2.3 (Content Chunking):**
```
EXPERIENCE section:
  Chunk 1: "Software Engineer at Google | 2022-Present | Remote - Led migration..."
  Chunk 2: "Data Scientist at Microsoft | 2020-2022 | Seattle, WA - Built recommendation..."
  
EDUCATION section:
  Chunk 1: "Bachelor of Technology in Computer Science | Indian Institute... | 2018-2022 | CGPA: 8.5/10"

SKILLS section:
  Chunk 1: "Languages: Python, Java, C++ | Frameworks: React, Django, FastAPI | Databases: PostgreSQL, MongoDB"

PERSONAL_INFO section:
  Chunk 1: "JOHN SMITH | john@test.com | +1-234-567-890 | linkedin.com/in/johnsmith"
```

**Step 3 (Classification & Entities):**
```
Chunk 0 (Personal Info):
  - Detected: email, phone, linkedin → +0.35 to personal_info
  - Section prior "JOHN SMITH" area → +0.25 to personal_info
  - Final: category=personal_info, confidence=0.92
  - Extracted: name="John Smith", email="john@test.com", phone="+1-234-567-890", linkedin="linkedin.com/in/..."
  - needs_review: False

Chunk 1 (Education):
  - Detected: "Bachelor", "2018-2022", "Institute", "CGPA" → matches education patterns
  - Confidence: 0.88
  - Extracted: institution="IIT Delhi", degree="B.Tech", field="Computer Science", start_year="2018", end_year="2022"
  - needs_review: False

Chunk 2 (Experience #1):
  - Detected: "Engineer at Google", "2022-Present", "Remote", date range
  - Keywords: "engineer", "company" → experience hints
  - Confidence: 0.91
  - Extracted: role="Software Engineer", company="Google", duration="2022-Present", location="Remote"
  - Key points: ["Led migration of 10M+ records...", "Improved query performance..."]
  - needs_review: False

Chunk 3 (Experience #2):
  - Similar scoring, confidence: 0.89
  - Extracted: role="Data Scientist", company="Microsoft", duration="2020-2022", location="Seattle, WA"
  - needs_review: False

Chunk 4 (Skills):
  - Category: skills, confidence: 0.95
  - Extracted: skills = {
      "languages": ["Python", "Java", "C++"],
      "frameworks": ["React", "Django", "FastAPI"],
      "databases": ["PostgreSQL", "MongoDB"]
    }
  - needs_review: False
```

**Step 5 (Embedding & Storage):**
```
5 chunks stored in Weaviate with embeddings:
- Each chunk's text embedded to 384-dim vector
- Metadata indexed for search filtering
- Example search query: "I need a Python developer"
  → Matches Chunk 0 (person) + Chunk 4 (skills)
  → Semantic similarity scoring
  → Returns ranked results
```

---

## 🎯 Key Design Decisions & Trade-offs

| Decision | Reasoning | Trade-off |
|----------|-----------|-----------|
| **Rule-based chunking first** | Fast, deterministic, no API costs | Misses context nuances (fixed by LLM review) |
| **LLM review only on low-conf** | Saves API calls, focuses review efforts | Some errors slip through if conf threshold wrong |
| **Section-based categories** | Aligns with resume structure | Limited to predefined 10 categories (can't extend easily) |
| **Regex entity extraction** | Simple, fast, interpretable | Fragile to format variations (partially mitigated by flexibility) |
| **all-MiniLM embeddings** | Lightweight, fast, good for semantic search | Only 384 dims (limited expressiveness vs 1536-dim models) |
| **Weaviate vector DB** | Easy setup, built-in filtering, multi-tenancy | Overkill for small datasets |

---

## 🔧 Current Limitations & Areas for Improvement

### **Limitation 1: Fixed Category Set**
Current system supports only 10 predefined categories. Resume with "Languages" section gets mapped to existing category or marked "other".

**Suggested Fix:** Dynamic category discovery using LLM

---

### **Limitation 2: Brittle Regex Extraction**
Entity extraction relies on regex patterns. Variations in formatting break extraction.

Example:
```
✓ Works:  "Software Engineer at Google"
✗ Fails:  "Software Engineer
           at Google"
           
✓ Works:  "2020-2022"
✗ Fails:  "2020 - 2022"  (spaces around dash)
```

**Suggested Fix:** Use flexible NER model for entity extraction

---

### **Limitation 3: Section Heading Detection**
Section detection uses heuristics. Unusual formatting (no heading, inline sections) causes mis-chunking.

**Suggested Fix:** Use layout-aware parsing (for PDFs) or fine-tuned heading detector

---

### **Limitation 4: Category Confidence Threshold**
Fixed 0.55 confidence threshold for LLM review. May flag some correct classifications as ambiguous.

**Suggested Fix:** Adaptive thresholds per category based on historical accuracy

---

### **Limitation 5: Entity-to-Form-Field Mapping**
Currently maps entities to **semantic field names** (e.g., "company", "role"). But actual form fields in templates might differ (e.g., "employer_name", "job_title").

**Suggested Fix:** Learn mapping from user feedback or template metadata

---

## 📈 Performance Metrics to Track

```yaml
Chunking Quality:
  - Accuracy of category classification (per category)
  - F1 score for entity extraction
  - LLM review override rate
  - Manual review requirement rate

System Performance:
  - Average processing time per file
  - Cost per file (API calls to Groq)
  - Vector search latency
  - Storage efficiency (chunks per GB)
```

---

## 🚀 Potential Enhancements (For Discussion)

1. **Multi-Modal Chunking**
   - Extract from images (logos, charts in resumes)
   - Use layout analysis for better section detection

2. **Adaptive Thresholds**
   - Per-category confidence thresholds
   - Progressive refinement based on feedback

3. **Hierarchical Chunking**
   - Main chunks (sections) + sub-chunks (items within sections)
   - Better for complex nested structure

4. **Context-Aware Embedding**
   - Use section context when embedding (vs global embedding)
   - Improves semantic search relevance

5. **Few-Shot Learning**
   - Show LLM examples of "good" vs "bad" classifications
   - Improves consistency

6. **User Feedback Loop**
   - Log user corrections
   - Fine-tune classification rules/thresholds
   - Identify common failure modes

---

## 📝 Code Location Reference

| Component | File Path |
|-----------|-----------|
| Upload endpoint | `Backend/router/features/upload/main.py` |
| Text extraction | `Backend/router/features/upload/main.py` - `extract_text_from_file()` |
| Semantic chunker | `Backend/Chunking/semantic_chunking.py` - `ResumeSemanticChunker` |
| LLM reviewer | `Backend/Chunking/llm_reviewer.py` - `review_needs_review_chunks()` |
| Vector DB | `Backend/router/features/retrieval/vector_db.py` |
| Data models | `Backend/models/vectorised_file.py` |
| Main app | `Backend/main.py` |

---

## ✅ Ready for College Presentation!

This document provides:
- ✅ Clear visual architecture diagram
- ✅ Step-by-step breakdown of algorithm
- ✅ Concrete example with real data flow
- ✅ Trade-off analysis
- ✅ Known limitations
- ✅ Improvement suggestions

**Questions for your college friend to discuss:**
1. How would you improve classification confidence for ambiguous resumes?
2. What if a resume has non-traditional sections (e.g., "Volunteer Work" or "Publications")?
3. How would you handle multi-language resumes?
4. Is the LLM review cost justified? How to optimize?
5. Can you design a feedback loop to continuously improve chunking?
