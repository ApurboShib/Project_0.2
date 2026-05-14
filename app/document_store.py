"""
Document Store - Simple file-based persistence for processed documents.
Stores processed document metadata, drafts, and edit history.
"""

import json
import uuid
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

STORE_DIR = Path("/tmp/legal_ai_store")


class DocumentStore:
    """Persists processed documents, drafts, and metadata to disk."""

    def __init__(self, store_dir: str = str(STORE_DIR)):
        self.store_dir = Path(store_dir)
        self.docs_dir = self.store_dir / "documents"
        self.drafts_dir = self.store_dir / "drafts"
        self.raw_dir = self.store_dir / "raw"
        for d in [self.docs_dir, self.drafts_dir, self.raw_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def save_document(self, processed_doc, raw_bytes: bytes = None) -> str:
        doc_id = processed_doc.doc_id
        path = self.docs_dir / f"{doc_id}.json"
        with open(path, "w") as f:
            json.dump(processed_doc.to_dict(), f, indent=2)

        if raw_bytes:
            raw_path = self.raw_dir / f"{doc_id}.bin"
            with open(raw_path, "wb") as f:
                f.write(raw_bytes)

        logger.info(f"Saved document {doc_id}")
        return doc_id

    def get_document(self, doc_id: str) -> Optional[dict]:
        path = self.docs_dir / f"{doc_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def list_documents(self) -> list:
        docs = []
        for path in sorted(self.docs_dir.glob("*.json")):
            try:
                with open(path) as f:
                    data = json.load(f)
                docs.append(
                    {
                        "doc_id": data["doc_id"],
                        "filename": data["filename"],
                        "total_pages": data["total_pages"],
                        "word_count": data["word_count"],
                        "doc_type": data["structured"]["document_type"],
                        "processing_notes": data.get("processing_notes", []),
                    }
                )
            except Exception as e:
                logger.warning(f"Could not read {path}: {e}")
        return docs

    def delete_document(self, doc_id: str) -> bool:
        path = self.docs_dir / f"{doc_id}.json"
        if path.exists():
            path.unlink()
            raw_path = self.raw_dir / f"{doc_id}.bin"
            if raw_path.exists():
                raw_path.unlink()
            return True
        return False

    def save_draft(self, draft_result) -> str:
        draft_id = draft_result.draft_id
        path = self.drafts_dir / f"{draft_id}.json"
        with open(path, "w") as f:
            json.dump(draft_result.to_dict(), f, indent=2)
        return draft_id

    def get_draft(self, draft_id: str) -> Optional[dict]:
        path = self.drafts_dir / f"{draft_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            return json.load(f)

    def list_drafts(self) -> list:
        drafts = []
        for path in sorted(self.drafts_dir.glob("*.json"), reverse=True):
            try:
                with open(path) as f:
                    data = json.load(f)
                drafts.append(
                    {
                        "draft_id": data["draft_id"],
                        "title": data["title"],
                        "draft_type": data["draft_type"],
                        "draft_type_label": data["draft_type_label"],
                        "doc_ids": data["doc_ids"],
                        "word_count": data["word_count"],
                    }
                )
            except Exception as e:
                logger.warning(f"Could not read {path}: {e}")
        return drafts

    def update_draft_content(self, draft_id: str, new_content: str) -> bool:
        draft = self.get_draft(draft_id)
        if not draft:
            return False
        draft["content"] = new_content
        draft["word_count"] = len(new_content.split())
        path = self.drafts_dir / f"{draft_id}.json"
        with open(path, "w") as f:
            json.dump(draft, f, indent=2)
        return True

    @staticmethod
    def generate_id(prefix: str = "") -> str:
        short = uuid.uuid4().hex[:10]
        return f"{prefix}{short}" if prefix else short
