# 🎯 INTERVIEW GUIDE - Legal Drafting Assistant

## Quick Overview (60 seconds)

**Project**: A full-stack AI system for processing legal documents with semantic search, Claude-powered drafting, and intelligent learning.

**Tech Stack**: Python (FastAPI), JavaScript (Vanilla), SQLite, ChromaDB, Claude API

**Key Achievement**: Designed a production-ready application that processes documents, generates grounded AI drafts with citations, and learns from user feedback.

---

## 1. ARCHITECTURE EXPLANATION (Interview Answer)

### High-Level Flow

```
User Upload Document
    ↓
[Document Processing]
    - PDF/Text extraction with pypdf
    - Text cleaning and normalization
    - Structured field extraction (dates, parties, amounts)
    ↓
[Semantic Search]
    - Chunk document into overlapping segments
    - Generate embeddings with ChromaDB
    - Create searchable vector database
    ↓
[AI Draft Generation]
    - Build evidence-grounded prompt
    - Send to Claude API with instructions
    - Generate draft with citations [Evidence N]
    ↓
[Display Results]
    - Show draft with evidence sources
    - Allow user to edit
    ↓
[Learning System]
    - Analyze user edits (diff computation)
    - Extract style patterns via Claude
    - Store rules for future use
    ↓
[Persistence]
    - SQLite stores metadata
    - ChromaDB stores vectors
    - File store preserves originals
```

### Why This Design?

- **Modular**: Each component (processing, retrieval, generation, learning) is independent
- **Scalable**: Can add new draft types or LLM providers without refactoring
- **Learnable**: System improves from user feedback
- **Persistent**: Maintains history across sessions
- **Grounded**: All claims backed by evidence (no hallucinations)

---

## 2. KEY CODE EXAMPLES FOR INTERVIEWS

### Example 1: Document Processing with Fallback Chain

```python
# app/document_processor.py - Shows progressive enhancement
def _extract_page(self, page, page_num, notes) -> ExtractedPage:
    # Try 1: Native PDF text
    raw_text = page.extract_text()
    cleaned = self._clean_text(raw_text)

    if len(cleaned) >= self.MIN_CHARS_FOR_NATIVE:
        return ExtractedPage(
            page_num=page_num,
            cleaned_text=cleaned,
            extraction_method="native_pdf",  # Success!
            confidence="high"
        )

    # Try 2: Claude Vision OCR (for scanned pages)
    if self.anthropic:
        ocr_text = self._vision_ocr_pypdf(page, page_num)
        if ocr_text:
            return ExtractedPage(..., extraction_method="ocr_fallback")

    # Fallback: Mark as empty, continue processing
    return ExtractedPage(..., extraction_method="empty")
```

**Why This Matters**:

- Shows practical problem-solving
- Demonstrates error handling
- Proves you understand edge cases
- Shows knowledge of OCR as fallback

---

### Example 2: Grounded AI Drafting (No Hallucinations)

```python
# app/draft_generator.py - Shows prompt engineering
SYSTEM_PROMPT = """You are a legal document analyst.
Critical rules:
1. Every claim MUST be supported by evidence passages below
2. If information is NOT in the evidence, say "Not stated in documents"
3. For each major point, cite evidence: [Evidence 2]
4. Never invent facts or assume information
5. Flag gaps in source documents
"""

def _build_prompt(self, draft_type, chunks, instructions):
    evidence_text = self._format_evidence(chunks)

    return f"""{SYSTEM_PROMPT}

Evidence Passages:
{evidence_text}

Generate a {draft_type} that uses ONLY the evidence above.
Custom instructions: {instructions}
"""
```

**Why This Matters**:

- Shows prompt engineering skill
- Demonstrates constraint-based design
- Proves you prevent AI hallucinations
- Shows consideration of user needs (lawyers want trustworthy AI)

---

### Example 3: Semantic Search Implementation

```python
# app/retrieval.py - Shows data structure design
def retrieve(self, query, doc_ids=None, top_k=10):
    """Retrieve most relevant text chunks"""
    # ChromaDB automatically generates embeddings
    results = self.collection.query(
        query_texts=[query],
        n_results=top_k,
        where={"doc_id": {"$in": doc_ids}} if doc_ids else None
    )

    # Score results by relevance
    chunks_with_scores = []
    for i, (text, doc_id, distance) in enumerate(zip(...)):
        # ChromaDB returns distance; convert to similarity score
        relevance_score = 1 / (1 + distance)

        chunks_with_scores.append(ChunkWithScore(
            text=text,
            doc_id=doc_id,
            relevance_score=relevance_score,
            metadata={...}
        ))

    return sorted(chunks_with_scores,
                 key=lambda x: x.relevance_score,
                 reverse=True)
```

**Why This Matters**:

- Shows understanding of vector databases
- Demonstrates scoring/ranking logic
- Proves you can work with ML/AI infrastructure

---

### Example 4: Learning System (Edit Analysis)

```python
# app/edit_learner.py - Shows machine learning thinking
def analyze_edits(self, original, edited, draft_type):
    """Extract style rules from user edits"""
    # Compute diff
    diffs = difflib.unified_diff(
        original.splitlines(),
        edited.splitlines()
    )

    # Use Claude to extract PATTERNS not just text
    prompt = f"""Analyze these edits to a legal {draft_type}:

Original:
{original}

Edited:
{edited}

What STYLE PATTERNS did the user apply?
List 2-3 reusable rules for future drafts."""

    response = self.anthropic.messages.create(
        model="claude-sonnet-4-20250514",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text
```

**Why This Matters**:

- Shows machine learning thinking
- Demonstrates feedback loop design
- Proves you can extract patterns (key for AI systems)
- Shows meta-learning concepts

---

## 3. FRONTEND INTERVIEW TALKING POINTS

### Design Decisions

"I designed the frontend to be professional yet minimal:

- **Sticky navigation** with status indicators - User knows system health at a glance
- **Two-column layout** - Processing form on left, status on right (mobile-responsive)
- **Modal results** - Full-screen, uncluttered view of results
- **Clear microcopy** - Labels, hints, and tooltips guide users
- **Smooth animations** - Fade-in/slide-up animations for polish"

### Responsive Design

"The CSS uses:

- **CSS Variables** for theming (24 properties)
- **Grid/Flexbox** for layout
- **Media queries** for responsive design
- **No external frameworks** - vanilla CSS for control and minimal bundle size"

### Code Quality in Frontend

"I used:

- **Section comments** (22+ dividers) for navigation
- **Descriptive class names** (e.g., `btn-primary`, `card-header`)
- **Semantic HTML** for accessibility
- **Clean JavaScript** with clear function names
- **Event delegation** for efficient handling"

---

## 4. DATABASE DESIGN INTERVIEW

### Schema Explanation

```
DOCUMENTS table:
- Stores extracted text and metadata
- doc_id (UUID) as primary key
- Enables searching/filtering across documents

DRAFTS table:
- Stores generated content
- References doc_ids (many-to-many)
- Tracks draft_type for learning

EDITS table:
- Captures user feedback
- Original vs edited content
- Extracted rules from diff

RULES table (Learning):
- Learned style patterns
- Frequency count (confidence measure)
- Draft-type specific
```

### Why This Structure?

- **Normalized** - No redundant data
- **Queryable** - Easy to find docs/drafts
- **Learnable** - Rules table captures patterns
- **Auditable** - Full history preserved

---

## 5. PROBLEM-SOLVING EXAMPLES

### Challenge 1: "How do you prevent hallucinations?"

**Answer**:
"I implemented constraint-based prompting:

1. System prompt explicitly forbids making up information
2. Evidence passages provided to Claude
3. User must cite [Evidence N] for claims
4. All uncited claims marked 'Not stated in documents'
5. System tracks which evidence was used"

### Challenge 2: "What if the PDF is scanned/unreadable?"

**Answer**:
"Progressive fallback chain:

1. Try native PDF text extraction
2. If sparse/low quality → Use Claude Vision OCR
3. If Claude OCR fails → Mark page as low-confidence
4. Continue processing remaining pages
5. Alert user about low-quality pages in report"

### Challenge 3: "How do you handle multiple document types?"

**Answer**:
"Abstracted interface:

- DocumentProcessor class handles any format
- Detects file type automatically
- Routes to appropriate handler (PDF/TXT/MD)
- Returns standardized ProcessedDocument object
- Easy to add new formats by extending base class"

### Challenge 4: "How would you scale this to millions of documents?"

**Answer**:
"Production scaling:

- **Database**: SQLite → PostgreSQL (supports parallel queries)
- **Vector Store**: ChromaDB → Pinecone/Weaviate (managed service)
- **API**: Single worker → Multiple workers (Gunicorn/Kubernetes)
- **Processing**: Synchronous → Async job queue (Celery)
- **Caching**: Add Redis for rule caching
- **Monitoring**: Add Sentry/DataDog for errors"

---

## 6. QUICK TECHNICAL DEEP DIVES

### How Semantic Search Works

"ChromaDB takes text chunks, generates embeddings (numerical representations),
then finds similar embeddings to the query using vector similarity.
Higher dot product = more similar. This way we find relevant evidence
without keyword matching."

### Why Multiple Draft Types?

"Different document types need different structures:

- **Case Summary** - Chronological facts
- **Memo** - TO/FROM/RE structure
- **Notice** - Key dates and obligations
- **Checklist** - Verification items
- **Title Review** - Property/document specifics

Users pick the type that fits their need."

### Edit Learning Design

"When user edits a draft:

1. I compute diff (what changed)
2. Send to Claude: 'What style patterns do these edits represent?'
3. Claude extracts rules (not just text changes)
4. Store in database with frequency counter
5. Next draft of same type → inject learned rules into prompt
   This trains the model on user preferences."

---

## 7. WHAT TO EMPHASIZE

### ✅ DO MENTION:

- "I chose pypdf to avoid compilation issues (SSL)"
- "I abstracted storage (SQLite + ChromaDB + file store)"
- "I implemented fallback chains for robustness"
- "I separated concerns (processing ≠ drafting ≠ learning)"
- "I designed for extensibility (easy to add draft types)"
- "I made the UI professional and responsive"
- "I documented everything for maintenance"

### ✅ DO EXPLAIN:

- Why each technology choice (pypdf over PyMuPDF)
- How the learning system works
- Why grounding prevents hallucinations
- How semantic search improves over keyword search
- The modular architecture benefits

### ❌ DON'T OVER-EXPLAIN:

- Every single line of code
- Every CSS property
- Every HTML element
- Generic technology facts (only relevant ones)

---

## 8. INTERVIEW PRACTICE QUESTIONS

### Q1: "Walk me through the system from document upload to draft generation"

**Your Answer Should Cover**:

- File upload validation
- Document processing pipeline
- Semantic search retrieval
- Prompt building with evidence
- Claude API call
- Result formatting and storage

### Q2: "How do you ensure the AI doesn't make things up?"

**Your Answer Should Cover**:

- Explicit system prompt constraints
- Evidence-based prompting
- Citation requirements
- "Not stated in documents" handling
- Testing/verification approach

### Q3: "What's the learning system and how does it work?"

**Your Answer Should Cover**:

- Edit capture mechanism
- Diff analysis
- Pattern extraction via Claude
- Rule storage and frequency
- Rule injection in future prompts

### Q4: "How would you test this system?"

**Your Answer Should Cover**:

- Unit tests for each module
- Integration tests for workflows
- Test documents with known outputs
- Verification of learned rules
- Performance benchmarks

### Q5: "What would you improve in a production version?"

**Your Answer Should Cover**:

- Async processing for large docs
- Database indexing for scale
- Caching for performance
- Monitoring and alerting
- User authentication
- API rate limiting

---

## 9. TECHNICAL STRENGTHS TO HIGHLIGHT

### Backend Architecture

✅ Modular design (10 Python modules)
✅ Clear separation of concerns
✅ Layered architecture (UI → API → Logic → DB)
✅ Type hints throughout
✅ Error handling with meaningful messages
✅ Configuration management

### AI/LLM Integration

✅ Prompt engineering (constraint-based)
✅ Prevents hallucinations (grounding)
✅ Falls back to vision OCR
✅ Learns from feedback
✅ Multi-step reasoning

### Database Design

✅ Normalized schema
✅ Multiple storage types
✅ Persistence across sessions
✅ Learning storage

### Frontend

✅ Professional UI design
✅ Responsive layout
✅ Smooth animations
✅ Clear UX
✅ Accessibility

### Code Quality

✅ Well-documented
✅ Clean formatting
✅ Best practices
✅ Production-ready

---

## 10. CLOSING STATEMENT

"I built a complete AI system that demonstrates:

- Full-stack development (Python backend + JavaScript frontend)
- LLM integration with careful constraint design
- Semantic search and vector databases
- Data persistence patterns
- Professional UI/UX
- Scalable, modular architecture
- Production-quality code

The system processes legal documents, generates grounded AI drafts with evidence citations,
and learns from user feedback to improve over time. Every component is designed for
reliability, extensibility, and real-world use."

---

## FILES TO REFERENCE IN INTERVIEW

When asked "Show me...", reference:

- **Architecture**: README.md (visual flow)
- **Module Design**: app/main.py (10+ endpoints)
- **AI Grounding**: app/draft_generator.py (SYSTEM_PROMPT)
- **Learning**: app/edit_learner.py (extract_rules function)
- **Frontend**: app/templates/index.html (professional design)
- **Database**: app/storage.py (schema creation)
- **Process Flow**: app/document_processor.py (fallback chain)

---

## GOOD LUCK! 🎯

You built a solid, professional project. Know your code, be able to explain
the design decisions, and talk confidently about the tradeoffs you made.

Focus on: **What problem does this solve?** and **Why did you make that choice?**

The answers are all in your code. You've got this! 💪
