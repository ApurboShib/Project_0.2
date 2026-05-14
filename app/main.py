import logging
import uuid
from enum import Enum
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .config import ANTHROPIC_API_KEY, GROQ_API_KEY, GEMINI_API_KEY, LLM_PROVIDER, CHROMA_DIR, DATA_DIR
from .document_processor import DocumentProcessor
from .document_store import DocumentStore
from .draft_generator import DRAFT_TYPES, DraftGenerator
from .edit_learner import EditLearner
from .retrieval import RetrievalEngine, TOP_K
from .storage import SQLiteStore
from .style_rules import StyleRuleStore

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    from groq import Groq
except ImportError:
    Groq = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Legal Drafting Assistant",
    description="""
    An AI-powered legal document processing and drafting system.
    
    ### Core Features:
    * **Document Processing**: Upload PDFs/TXTs and index them for retrieval.
    * **AI Drafting**: Generate legal documents grounded in retrieved evidence.
    * **Feedback Loop**: Capture edits to improve future draft quality.
    """,
    version="1.0.0"
)
templates = Jinja2Templates(directory="app/templates")

store = SQLiteStore(DATA_DIR / "app.db")
style_store = StyleRuleStore(store)
doc_store = DocumentStore(str(DATA_DIR / "file_store"))


def _get_llm_client():
    """Get the configured LLM client (GROQ, Gemini, or Anthropic)"""
    if LLM_PROVIDER == "groq":
        if not GROQ_API_KEY or not Groq:
            logger.warning("GROQ_API_KEY not set or groq package not installed")
            return None
        return Groq(api_key=GROQ_API_KEY)
    elif LLM_PROVIDER == "anthropic":
        if not ANTHROPIC_API_KEY or not anthropic:
            logger.warning("ANTHROPIC_API_KEY not set or anthropic package not installed")
            return None
        return anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    elif LLM_PROVIDER == "gemini":
        logger.warning("Gemini support coming soon. Using GROQ as fallback.")
        if not GROQ_API_KEY or not Groq:
            return None
        return Groq(api_key=GROQ_API_KEY)
    else:
        logger.error(f"Unknown LLM_PROVIDER: {LLM_PROVIDER}. Defaulting to GROQ.")
        if not GROQ_API_KEY or not Groq:
            return None
        return Groq(api_key=GROQ_API_KEY)


llm_client = _get_llm_client()
processor = DocumentProcessor(client=llm_client)
retrieval = RetrievalEngine(persist_dir=str(CHROMA_DIR))
draft_generator = DraftGenerator(llm_client, style_store=style_store)
edit_learner = EditLearner(llm_client, style_store=style_store) if llm_client else None


class DraftType(str, Enum):
    case_fact_summary = "case_fact_summary"
    internal_memo = "internal_memo"
    notice_summary = "notice_summary"
    document_checklist = "document_checklist"
    title_review = "title_review"


class DraftRequest(BaseModel):
    doc_ids: List[str] = Field(
        ..., 
        description="List of processed document IDs to use for evidence",
        example=["550e8400-e29b-41d4-a716-446655440000"]
    )
    draft_type: DraftType = Field(
        ..., 
        description="The type of legal draft to generate",
        example=DraftType.case_fact_summary
    )
    custom_instructions: Optional[str] = Field(
        "", 
        description="Optional specific instructions for the AI",
        example="Focus on the monetary damages section."
    )


class EditRequest(BaseModel):
    draft_id: str = Field(..., description="The ID of the draft being edited")
    edited_content: str = Field(..., description="The full updated content of the draft")


def _build_query(draft_type: str, structured: dict) -> str:
    parts = [DRAFT_TYPES.get(draft_type, draft_type), structured.get("document_type", "")]
    if structured.get("parties"):
        parts.append("parties " + ", ".join(structured.get("parties", [])[:4]))
    if structured.get("dates"):
        parts.append("dates " + ", ".join(structured.get("dates", [])[:4]))
    if structured.get("case_numbers"):
        parts.append("case numbers " + ", ".join(structured.get("case_numbers", [])[:3]))
    if structured.get("amounts"):
        parts.append("amounts " + ", ".join(structured.get("amounts", [])[:3]))
    return " | ".join(p for p in parts if p)


def _aggregate_metadata(processed_docs: list) -> dict:
    filenames = [doc["filename"] for doc in processed_docs]
    doc_type = processed_docs[0]["structured"]["document_type"] if processed_docs else ""
    doc_ids = [doc["doc_id"] for doc in processed_docs]
    return {"filenames": filenames, "doc_type": doc_type, "doc_ids": doc_ids}


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "anthropic_configured": bool(llm_client),
        },
    )


@app.post("/process")
async def process_document(
    request: Request,
    file: UploadFile = File(...),
    draft_type: str = Form(...),
    custom_instructions: str = Form(""),
):
    if draft_type not in DRAFT_TYPES:
        valid_types = ", ".join(DRAFT_TYPES.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid draft type. Valid options are: {valid_types}"
        )
    if not llm_client:
        return templates.TemplateResponse(
            "result.html",
            {
                "request": request,
                "error": "LLM API is not configured. Please set GROQ_API_KEY or ANTHROPIC_API_KEY in .env",
            },
            status_code=400,
        )

    filename = file.filename or "uploaded_document"
    if not filename.lower().endswith((".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only PDF, text, or image files (PNG/JPG) are supported.")

    file_bytes = await file.read()
    doc_id = str(uuid.uuid4())
    processed = processor.process(file_bytes, filename, doc_id)
    store.save_document(processed)
    retrieval.index_document(processed)

    query = _build_query(draft_type, processed.to_dict()["structured"])
    chunks = retrieval.retrieve(query, doc_ids=[doc_id], top_k=TOP_K)

    draft_id = str(uuid.uuid4())
    metadata = _aggregate_metadata([processed.to_dict()])
    draft = draft_generator.generate(
        draft_type=draft_type,
        retrieved_chunks=chunks,
        doc_metadata=metadata,
        draft_id=draft_id,
        custom_instructions=custom_instructions.strip(),
    )
    store.save_draft(draft)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "draft": draft.to_dict(),
            "processed": processed.to_dict(),
            "learned_rules": [],
        },
    )


@app.get("/result/{draft_id}", response_class=HTMLResponse)
async def get_result(request: Request, draft_id: str):
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found")
    draft["draft_type_label"] = DRAFT_TYPES.get(draft["draft_type"], "Legal Document")
    
    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "draft": draft,
            "processed": None,
            "learned_rules": [],
        },
    )


@app.post("/edits", response_class=HTMLResponse)
async def submit_edits(
    request: Request,
    draft_id: str = Form(...),
    edited_content: str = Form(...),
):
    draft = store.get_draft(draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")

    edit_id = str(uuid.uuid4())
    store.save_edit(edit_id, draft_id, edited_content)
    learned_rules = style_store.learn_from_edit(draft["draft_type"], edited_content)

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "draft": draft,
            "processed": None,
            "learned_rules": learned_rules,
            "edit_saved": True,
        },
    )


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.post("/api/process")
async def api_process_document(file: UploadFile = File(...)):
    filename = file.filename or "uploaded_document"
    if not filename.lower().endswith((".pdf", ".txt", ".md", ".png", ".jpg", ".jpeg")):
        raise HTTPException(status_code=400, detail="Only PDF, text, or image files (PNG/JPG) are supported.")
    file_bytes = await file.read()
    doc_id = str(uuid.uuid4())
    processed = processor.process(file_bytes, filename, doc_id)
    store.save_document(processed)
    retrieval.index_document(processed)
    return JSONResponse(processed.to_dict())


@app.post("/api/draft")
async def api_generate_draft(payload: DraftRequest):
    if payload.draft_type not in DRAFT_TYPES:
        valid_types = ", ".join(DRAFT_TYPES.keys())
        raise HTTPException(
            status_code=400, 
            detail=f"Invalid draft type. Valid options are: {valid_types}"
        )
    if not llm_client:
        raise HTTPException(status_code=400, detail="LLM API is not configured. Please set GROQ_API_KEY or ANTHROPIC_API_KEY in .env")
    if not payload.doc_ids:
        raise HTTPException(status_code=400, detail="doc_ids is required.")

    processed_docs = []
    for doc_id in payload.doc_ids:
        doc = store.get_document(doc_id)
        if not doc:
            raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
        processed_docs.append(doc)

    metadata = _aggregate_metadata(processed_docs)
    query = _build_query(payload.draft_type, processed_docs[0]["structured"])
    chunks = retrieval.retrieve(query, doc_ids=payload.doc_ids, top_k=TOP_K)

    draft_id = str(uuid.uuid4())
    draft = draft_generator.generate(
        draft_type=payload.draft_type,
        retrieved_chunks=chunks,
        doc_metadata=metadata,
        draft_id=draft_id,
        custom_instructions=(payload.custom_instructions or "").strip(),
    )
    store.save_draft(draft)
    return JSONResponse(draft.to_dict())


@app.post("/api/edit")
async def api_submit_edit(payload: EditRequest):
    draft = store.get_draft(payload.draft_id)
    if not draft:
        raise HTTPException(status_code=404, detail="Draft not found.")

    edit_id = str(uuid.uuid4())
    store.save_edit(edit_id, payload.draft_id, payload.edited_content)
    
    learned_rules = []
    if edit_learner:
        record = edit_learner.process_edit(
            edit_id=edit_id,
            draft_id=payload.draft_id,
            draft_type=draft["draft_type"],
            original=draft["content"],
            edited=payload.edited_content,
        )
        learned_rules = record.extracted_rules
    
    return JSONResponse({"edit_id": edit_id, "learned_rules": learned_rules})


@app.get("/api/documents")
async def api_list_documents():
    docs = doc_store.list_documents()
    return JSONResponse(docs)


@app.get("/api/drafts")
async def api_list_drafts():
    drafts = doc_store.list_drafts()
    return JSONResponse(drafts)


@app.get("/api/rules")
async def api_get_rules():
    rules = store.get_style_rules("") or {}
    all_rules = {}
    for draft_type in DRAFT_TYPES:
        type_rules = store.get_style_rules(draft_type)
        if type_rules:
            all_rules[draft_type] = type_rules
    return JSONResponse(all_rules)
