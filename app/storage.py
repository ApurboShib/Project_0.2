import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional


class SQLiteStore:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        cur = self.conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                doc_id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                processed_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS drafts (
                draft_id TEXT PRIMARY KEY,
                doc_ids TEXT NOT NULL,
                draft_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                evidence_json TEXT NOT NULL,
                model_used TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS edits (
                edit_id TEXT PRIMARY KEY,
                draft_id TEXT NOT NULL,
                edited_content TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS style_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                draft_type TEXT NOT NULL,
                rule_text TEXT NOT NULL,
                frequency INTEGER NOT NULL DEFAULT 1,
                last_seen TEXT NOT NULL,
                UNIQUE(draft_type, rule_text)
            );
            """
        )
        self.conn.commit()

    def save_document(self, processed_doc) -> None:
        payload = json.dumps(processed_doc.to_dict())
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO documents (doc_id, filename, processed_json, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                processed_doc.doc_id,
                processed_doc.filename,
                payload,
                datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def get_document(self, doc_id: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute(
            "SELECT processed_json FROM documents WHERE doc_id = ?",
            (doc_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return json.loads(row["processed_json"])

    def save_draft(self, draft) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT OR REPLACE INTO drafts
            (draft_id, doc_ids, draft_type, title, content, evidence_json, model_used, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                draft.draft_id,
                json.dumps(draft.doc_ids),
                draft.draft_type,
                draft.title,
                draft.content,
                json.dumps(draft.evidence_used),
                draft.model_used,
                datetime.utcnow().isoformat(),
            ),
        )
        self.conn.commit()

    def get_draft(self, draft_id: str) -> Optional[dict]:
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM drafts WHERE draft_id = ?", (draft_id,))
        row = cur.fetchone()
        if not row:
            return None
        return {
            "draft_id": row["draft_id"],
            "doc_ids": json.loads(row["doc_ids"]),
            "draft_type": row["draft_type"],
            "title": row["title"],
            "content": row["content"],
            "evidence_used": json.loads(row["evidence_json"]),
            "model_used": row["model_used"],
        }

    def save_edit(self, edit_id: str, draft_id: str, edited_content: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO edits (edit_id, draft_id, edited_content, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (edit_id, draft_id, edited_content, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def upsert_style_rule(self, draft_type: str, rule_text: str) -> None:
        cur = self.conn.cursor()
        cur.execute(
            """
            INSERT INTO style_rules (draft_type, rule_text, frequency, last_seen)
            VALUES (?, ?, 1, ?)
            ON CONFLICT(draft_type, rule_text) DO UPDATE SET
                frequency = frequency + 1,
                last_seen = excluded.last_seen
            """,
            (draft_type, rule_text, datetime.utcnow().isoformat()),
        )
        self.conn.commit()

    def get_style_rules(self, draft_type: str) -> list:
        cur = self.conn.cursor()
        cur.execute(
            """
            SELECT rule_text, frequency
            FROM style_rules
            WHERE draft_type = ?
            ORDER BY frequency DESC, rule_text ASC
            """,
            (draft_type,),
        )
        rows = cur.fetchall()
        return [{"rule_text": r["rule_text"], "frequency": r["frequency"]} for r in rows]

    def list_documents(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT processed_json FROM documents ORDER BY created_at DESC")
        docs = []
        for row in cur.fetchall():
            try:
                data = json.loads(row["processed_json"])
                docs.append({
                    "doc_id": data.get("doc_id", ""),
                    "filename": data.get("filename", ""),
                    "total_pages": data.get("total_pages", 0),
                    "word_count": data.get("word_count", 0),
                    "doc_type": data.get("structured", {}).get("document_type", ""),
                    "processing_notes": data.get("processing_notes", [])
                })
            except json.JSONDecodeError:
                pass
        return docs

    def list_drafts(self) -> list:
        cur = self.conn.cursor()
        cur.execute("SELECT draft_id, title, draft_type, doc_ids, content FROM drafts ORDER BY created_at DESC")
        drafts = []
        for row in cur.fetchall():
            try:
                doc_ids = json.loads(row["doc_ids"])
                content = row["content"]
                word_count = len(content.split()) if content else 0
                draft_type = row["draft_type"]
                drafts.append({
                    "draft_id": row["draft_id"],
                    "title": row["title"],
                    "draft_type": draft_type,
                    "draft_type_label": draft_type.replace("_", " ").title(),
                    "doc_ids": doc_ids,
                    "word_count": word_count
                })
            except Exception:
                pass
        return drafts
