# Legal Drafting Assistant

**End-to-end AI system for processing messy legal documents, generating grounded drafts with evidence citations, and improving via operator feedback learning.**

## 🎯 What It Does

1. **Document Processing**: Extracts text from PDFs (via PyMuPDF), falls back to Claude vision OCR for scanned pages, and handles plain text files
2. **Semantic Retrieval**: Chunks documents and indexes them in ChromaDB for intelligent evidence retrieval
3. **Grounded Drafting**: Uses Claude to generate drafts that are strictly grounded in retrieved evidence with citations
4. **Feedback Loop**: Learns from operator edits to extract reusable style rules, improving future drafts

## 🏗️ Architecture

```
Document Upload
      ↓
  Processor (PyMuPDF + Vision OCR fallback)
      ↓
  Retrieval Engine (ChromaDB semantic search)
      ↓
  Draft Generator (Claude with grounding constraints)
      ↓
  Edit Learner (extracts style rules from operator feedback)
      ↓
  Style Rule Store (SQLite)
```

## 📋 Features

- **Multi-format support**: PDF, TXT, MD files
- **Smart extraction**: Native PDF + block-level + OCR fallback
- **5 draft types**: Case summaries, memos, notices, checklists, title reviews
- **Evidence citations**: Every claim backed by source with relevance scores
- **Style learning**: Automatic extraction of formatting & structure preferences
- **Full REST API**: Programmatic access to all features
- **Modern UI**: Responsive web interface with real-time status

## 🚀 Quick Start

### 1. Clone & Setup

```bash
cd /path/to/Project_02
chmod +x run.sh
./run.sh
```

### 2. Configure API Key

Edit `.env`:
```env
ANTHROPIC_API_KEY=sk-ant-...
LEGAL_AI_DATA_DIR=./data
```

### 3. Open in Browser

```
http://localhost:8000
```

## 📖 Usage

### Web UI

1. Upload a legal document (PDF/TXT/MD)
2. Select draft type
3. Add optional custom instructions
4. Click "Generate Draft"
5. Review evidence citations
6. Edit draft and save to learn style rules

### API

**Process a document:**
```bash
curl -X POST -F "file=@samples/sample_notice.txt" \
  http://localhost:8000/api/process
# Returns: {"doc_id": "...", "filename": "...", ...}
```

**Generate a draft:**
```bash
curl -X POST http://localhost:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{
    "doc_ids": ["doc-uuid-here"],
    "draft_type": "notice_summary",
    "custom_instructions": "Emphasize deadlines"
  }'
# Returns: {"draft_id": "...", "content": "...", "evidence_used": [...]}
```

**Submit edits and learn rules:**
```bash
curl -X POST http://localhost:8000/api/edit \
  -H "Content-Type: application/json" \
  -d '{
    "draft_id": "draft-uuid-here",
    "edited_content": "[your corrected draft]"
  }'
# Returns: {"edit_id": "...", "learned_rules": [...]}
```

**List all documents, drafts, and rules:**
```bash
curl http://localhost:8000/api/documents
curl http://localhost:8000/api/drafts
curl http://localhost:8000/api/rules
```

## 📁 Project Structure

```
app/
├── __init__.py
├── config.py                 # Environment & paths
├── document_processor.py      # PDF/text extraction
├── document_store.py          # File-based persistence
├── draft_generator.py         # Claude drafting
├── edit_learner.py            # Feedback learning
├── main.py                    # FastAPI routes
├── retrieval.py               # ChromaDB indexing
├── storage.py                 # SQLite storage
├── style_rules.py             # Rule management
├── templates/
│   ├── index.html             # Main UI
│   └── result.html            # Draft results
data/                          # Generated data (local)
samples/
├── sample_notice.txt          # Example input
└── sample_output.json         # Example output
```

## 📊 Data Storage

- **SQLite**: Documents, drafts, edits, learned rules → `data/app.db`
- **ChromaDB**: Vector embeddings → `data/chroma/`
- **File store**: Raw documents → `data/file_store/`

## 🎓 Draft Types

| Type | Use Case |
|------|----------|
| **case_fact_summary** | Litigation documents, complaints, briefs |
| **internal_memo** | Summaries for attorneys, working papers |
| **notice_summary** | Contract terminations, legal notices |
| **document_checklist** | Requirements tracking, compliance |
| **title_review** | Contract & property document analysis |

## 🔧 Advanced Options

### Custom Instructions

Add specific guidance per draft:
```
"Highlight any ambiguous language"
"Use table format for all comparisons"
"Flag missing signatures or dates"
```

### Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...          # Required for Claude calls
LEGAL_AI_DATA_DIR=./data               # Storage directory
```

### Running Without Auto-Reload

For production:
```bash
./run-api.sh
```

This runs with 2 workers for better performance.

## ✅ Testing

Sample workflow:
```bash
# 1. Upload sample notice
curl -X POST -F "file=@samples/sample_notice.txt" \
  http://localhost:8000/api/process | jq '.doc_id'

# 2. Generate draft (copy the doc_id from above)
curl -X POST http://localhost:8000/api/draft \
  -H "Content-Type: application/json" \
  -d '{"doc_ids":["<DOC_ID>"], "draft_type":"notice_summary"}' | jq '.'

# 3. Try editing and learning rules
curl -X POST http://localhost:8000/api/edit \
  -H "Content-Type: application/json" \
  -d '{"draft_id":"<DRAFT_ID>","edited_content":"[edited version]"}'
```

## 🧠 How Learning Works

When you edit a draft:
1. **Diff computation**: Line-by-line comparison of original vs edited
2. **Rule extraction**: Claude analyzes changes to extract generalizable patterns
3. **Rule storage**: Rules are tagged by draft type and frequency counted
4. **Re-injection**: Rules applied to future drafts of same type

Example rules learned:
- "Always include the contract execution date in the first paragraph"
- "Use 'the Company' instead of referring to party by full name"
- "Add a 'Next Steps' section at the end of internal memos"

## 📝 Assumptions & Design Choices

- **Single-doc focus**: UI processes one document at a time; API supports multi-doc queries
- **Vision OCR via Claude**: Higher quality for scanned pages vs local OCR
- **Lightweight feedback**: Extracts rules not full diffs (smaller storage, more interpretable)
- **No hallucination**: Drafts strictly grounded in evidence; gaps clearly marked
- **SQLite for rules**: Simple, embedded storage; scales to thousands of rules

## 🚨 Evaluation Criteria

- ✅ All evidence citations are accurate and found in source
- ✅ Extracted structured fields match document content
- ✅ Drafts respect learned style rules on subsequent generations
- ✅ UI is responsive and handles errors gracefully
- ✅ API endpoints return valid JSON with proper status codes

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "ANTHROPIC_API_KEY not configured" | Add key to `.env` and restart |
| "No chunks produced" | Document may be too short or low-confidence |
| "Retrieval returned no results" | Query didn't match document content well |
| Database locked | Remove `data/app.db` and restart |
| Port 8000 in use | Change port: `uvicorn app.main:app --port 8001` |

## 📦 Dependencies

- `anthropic`: Claude API
- `chromadb`: Vector database
- `fastapi`: Web framework
- `pydantic`: Data validation
- `pymupdf`: PDF extraction
- `sqlite3`: Built-in Python storage
- `uvicorn`: ASGI server

See `requirements.txt` for pinned versions.

## 📄 License

This is a demonstration implementation for the AI Engineer assessment. Use at your own discretion.
