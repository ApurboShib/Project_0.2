import base64
import io
import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Optional
from app.config import LLM_PROVIDER

from pypdf import PdfReader

logger = logging.getLogger(__name__)


@dataclass
class ExtractedPage:
    page_num: int
    raw_text: str
    cleaned_text: str
    char_count: int
    confidence: str  # "high", "medium", "low"
    extraction_method: str  # "native_pdf", "ocr_fallback", "empty", "plain_text"


@dataclass
class StructuredFields:
    document_type: str = "unknown"
    parties: list = field(default_factory=list)
    dates: list = field(default_factory=list)
    case_numbers: list = field(default_factory=list)
    amounts: list = field(default_factory=list)
    jurisdiction: str = ""
    key_clauses: list = field(default_factory=list)
    summary_hint: str = ""


@dataclass
class ProcessedDocument:
    doc_id: str
    filename: str
    total_pages: int
    pages: list  # List[ExtractedPage]
    full_text: str
    structured: StructuredFields
    word_count: int
    processing_notes: list = field(default_factory=list)

    def to_dict(self):
        return {
            "doc_id": self.doc_id,
            "filename": self.filename,
            "total_pages": self.total_pages,
            "pages": [asdict(p) for p in self.pages],
            "full_text": self.full_text,
            "structured": asdict(self.structured),
            "word_count": self.word_count,
            "processing_notes": self.processing_notes,
        }


class DocumentProcessor:
    """
    Processes legal PDFs with graceful degradation:
    1. Try native PDF text extraction (fastest, best quality)
    2. Fallback to page-level image + Claude vision OCR for scanned/noisy pages
    3. Mark low-confidence pages clearly for downstream handling

    Also supports plain text inputs for quick demos.
    """

    MIN_CHARS_FOR_NATIVE = 50  # below this -> treat page as image-only

    def __init__(self, client=None):
        self.client = client

    def process(self, file_bytes: bytes, filename: str, doc_id: str) -> ProcessedDocument:
        if filename.lower().endswith((".txt", ".md")):
            return self._process_plain_text(file_bytes, filename, doc_id)

        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            return self._process_image(file_bytes, filename, doc_id)

        notes = []
        pages = []

        try:
            pdf = PdfReader(io.BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Cannot open PDF: {e}")

        total_pages = len(pdf.pages)

        for page_num, page in enumerate(pdf.pages, 1):
            extracted = self._extract_page(page, page_num, notes)
            pages.append(extracted)

        full_text = "\n\n---PAGE BREAK---\n\n".join(
            p.cleaned_text for p in pages if p.cleaned_text.strip()
        )

        structured = self._extract_structured_fields(full_text)
        word_count = len(full_text.split())

        return ProcessedDocument(
            doc_id=doc_id,
            filename=filename,
            total_pages=total_pages,
            pages=pages,
            full_text=full_text,
            structured=structured,
            word_count=word_count,
            processing_notes=notes,
        )

    def _process_plain_text(
        self, file_bytes: bytes, filename: str, doc_id: str
    ) -> ProcessedDocument:
        raw_text = file_bytes.decode("utf-8", errors="ignore")
        cleaned = self._clean_text(raw_text)
        confidence = "high" if len(cleaned) >= self.MIN_CHARS_FOR_NATIVE else "medium"
        page = ExtractedPage(
            page_num=1,
            raw_text=raw_text,
            cleaned_text=cleaned,
            char_count=len(cleaned),
            confidence=confidence,
            extraction_method="plain_text",
        )
        structured = self._extract_structured_fields(cleaned)
        return ProcessedDocument(
            doc_id=doc_id,
            filename=filename,
            total_pages=1,
            pages=[page],
            full_text=cleaned,
            structured=structured,
            word_count=len(cleaned.split()),
            processing_notes=["Plain text input processed without OCR."],
        )

    def _extract_page(self, page, page_num: int, notes: list) -> ExtractedPage:
        raw_text = page.extract_text()
        if raw_text is None:
            raw_text = ""
        cleaned = self._clean_text(raw_text)

        if len(cleaned) >= self.MIN_CHARS_FOR_NATIVE:
            return ExtractedPage(
                page_num=page_num,
                raw_text=raw_text,
                cleaned_text=cleaned,
                char_count=len(cleaned),
                confidence="high",
                extraction_method="native_pdf",
            )

        if self.client:
            notes.append(f"Page {page_num}: sparse text, using vision OCR")
            # For PDF images, we'd need to extract the PIL image first.
            # PyPDF image extraction is a bit complex, but let's assume we can get bytes.
            # Simplified for now: only native image files are fully supported for vision OCR.
            # But we can try to pass the raw image if it's a single image page.
            ocr_text = self._vision_ocr_call(None, page_num, page)
            if ocr_text:
                cleaned_ocr = self._clean_text(ocr_text)
                return ExtractedPage(
                    page_num=page_num,
                    raw_text=ocr_text,
                    cleaned_text=cleaned_ocr,
                    char_count=len(cleaned_ocr),
                    confidence="medium",
                    extraction_method="ocr_fallback",
                )

        notes.append(f"Page {page_num}: could not extract text")
        return ExtractedPage(
            page_num=page_num,
            raw_text="",
            cleaned_text="[Page content could not be extracted]",
            char_count=0,
            confidence="low",
            extraction_method="empty",
        )

    def _process_image(self, file_bytes: bytes, filename: str, doc_id: str) -> ProcessedDocument:
        ocr_text = self._vision_ocr_call(file_bytes, 1)
        cleaned = self._clean_text(ocr_text or "[Image content could not be extracted]")
        page = ExtractedPage(
            page_num=1,
            raw_text=ocr_text or "",
            cleaned_text=cleaned,
            char_count=len(cleaned),
            confidence="high" if ocr_text else "low",
            extraction_method="vision_ocr",
        )
        structured = self._extract_structured_fields(cleaned)
        return ProcessedDocument(
            doc_id=doc_id,
            filename=filename,
            total_pages=1,
            pages=[page],
            full_text=cleaned,
            structured=structured,
            word_count=len(cleaned.split()),
            processing_notes=["Image processed via AI vision OCR."],
        )

    def _vision_ocr_call(self, img_bytes: Optional[bytes], page_num: int, pypdf_page=None) -> Optional[str]:
        try:
            if not img_bytes and pypdf_page:
                # Try to extract from pypdf page
                if pypdf_page.images:
                    img = pypdf_page.images[0]
                    img_io = io.BytesIO()
                    img.image.save(img_io, format="PNG")
                    img_bytes = img_io.getvalue()
            
            if not img_bytes:
                return None

            img_b64 = base64.standard_b64encode(img_bytes).decode()
            prompt = (
                "This is a page from a legal document. "
                "Please extract ALL visible text exactly as it appears in its native language (e.g., English, Bangla, etc.), "
                "preserving structure (headings, lists, paragraphs). "
                "If text is partially illegible, do your best and mark "
                "uncertain parts with [?]. Output only the extracted text."
            )

            if LLM_PROVIDER == "groq":
                resp = self.client.chat.completions.create(
                    model="llama-3.2-90b-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{img_b64}"},
                                },
                            ],
                        }
                    ],
                    max_tokens=2000,
                )
                return resp.choices[0].message.content
            else:
                # Anthropic fallback
                resp = self.client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=2000,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/png",
                                        "data": img_b64,
                                    },
                                },
                                {"type": "text", "text": prompt},
                            ],
                        }
                    ],
                )
                return resp.content[0].text
        except Exception as e:
            logger.warning(f"Vision OCR failed for page {page_num}: {e}")
            return None

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2014", "--").replace("\u2013", "-")
        text = text.replace("\x00", "").replace("\x0c", "\n")
        text = re.sub(r"[ \t]{2,}", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _extract_structured_fields(self, full_text: str) -> StructuredFields:
        s = StructuredFields()

        text_lower = full_text.lower()
        if any(k in text_lower for k in ["retainer agreement", "engagement letter"]):
            s.document_type = "retainer_agreement"
        elif any(
            k in text_lower
            for k in ["complaint", "plaintiff", "defendant", "cause of action"]
        ):
            s.document_type = "legal_complaint"
        elif any(k in text_lower for k in ["settlement", "release of claims"]):
            s.document_type = "settlement"
        elif any(k in text_lower for k in ["notice", "hereby notified", "notice of"]):
            s.document_type = "notice"
        elif any(k in text_lower for k in ["memo", "memorandum"]):
            s.document_type = "memo"
        elif any(k in text_lower for k in ["contract", "agreement", "whereas"]):
            s.document_type = "contract"
        elif any(k in text_lower for k in ["motion", "petition", "order"]):
            s.document_type = "court_filing"
        else:
            s.document_type = "legal_document"

        date_patterns = [
            r"\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b",
            r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b",
            r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        ]
        dates = set()
        for pat in date_patterns:
            dates.update(re.findall(pat, full_text, re.IGNORECASE))
        s.dates = sorted(list(dates))[:10]

        case_patterns = [
            r"\bCase\s+No\.?\s*[\w\-/]+",
            r"\bDocket\s+No\.?\s*[\w\-/]+",
            r"\bCivil\s+Action\s+No\.?\s*[\w\-/]+",
            r"\b\d{2}-[A-Z]{2,4}-\d{4,}\b",
        ]
        case_nums = set()
        for pat in case_patterns:
            case_nums.update(re.findall(pat, full_text, re.IGNORECASE))
        s.case_numbers = list(case_nums)[:5]

        amount_pat = r"\$[\d,]+(?:\.\d{2})?"
        s.amounts = list(set(re.findall(amount_pat, full_text)))[:10]

        party_patterns = [
            r"Plaintiff[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\n|,|;)",
            r"Defendant[:\s]+([A-Z][A-Za-z\s,\.]+?)(?:\n|,|;)",
            r"(?:between|by and between)\s+([A-Z][A-Za-z\s,\.]+?)\s+and\s+([A-Z][A-Za-z\s,\.]+?)(?:\n|,)",
        ]
        parties = set()
        for pat in party_patterns:
            matches = re.findall(pat, full_text)
            for m in matches:
                if isinstance(m, tuple):
                    parties.update(x.strip() for x in m)
                else:
                    parties.add(m.strip())
        s.parties = [p for p in list(parties) if 3 < len(p) < 80][:8]

        heading_pat = r"^([A-Z][A-Z\s]{5,60})$"
        headings = re.findall(heading_pat, full_text, re.MULTILINE)
        s.key_clauses = [h.strip() for h in headings if len(h.strip()) > 5][:10]

        first_para = full_text[:500].strip()
        s.summary_hint = first_para[:200] + ("..." if len(first_para) > 200 else "")

        return s
