import logging
from dataclasses import dataclass
from typing import Optional

import chromadb
from chromadb.utils import embedding_functions

logger = logging.getLogger(__name__)

CHUNK_SIZE = 400
CHUNK_OVERLAP = 80
TOP_K = 6


@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    filename: str
    page_num: int
    chunk_index: int
    text: str
    relevance_score: float
    metadata: dict


class RetrievalEngine:
    """
    Manages a ChromaDB collection per document set.
    Uses the default embedding function (all-MiniLM via chromadb's built-in).
    """

    def __init__(self, persist_dir: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.ef = embedding_functions.DefaultEmbeddingFunction()
        self._ensure_collection()

    def _ensure_collection(self):
        self.collection = self.client.get_or_create_collection(
            name="legal_documents",
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"},
        )

    def index_document(self, processed_doc) -> int:
        chunks = self._chunk_document(processed_doc)
        if not chunks:
            logger.warning(f"No chunks produced for {processed_doc.doc_id}")
            return 0

        ids = []
        documents = []
        metadatas = []

        for chunk in chunks:
            chunk_id = f"{processed_doc.doc_id}_chunk_{chunk['index']}"
            ids.append(chunk_id)
            documents.append(chunk["text"])
            metadatas.append(
                {
                    "doc_id": processed_doc.doc_id,
                    "filename": processed_doc.filename,
                    "page_num": chunk["page_num"],
                    "chunk_index": chunk["index"],
                    "doc_type": processed_doc.structured.document_type,
                    "total_pages": processed_doc.total_pages,
                }
            )

        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.upsert(
                ids=ids[i : i + batch_size],
                documents=documents[i : i + batch_size],
                metadatas=metadatas[i : i + batch_size],
            )

        logger.info(f"Indexed {len(ids)} chunks for {processed_doc.doc_id}")
        return len(ids)

    def retrieve(
        self,
        query: str,
        doc_ids: Optional[list] = None,
        top_k: int = TOP_K,
    ) -> list:
        where = None
        if doc_ids:
            if len(doc_ids) == 1:
                where = {"doc_id": doc_ids[0]}
            else:
                where = {"doc_id": {"$in": doc_ids}}

        count = self.collection.count()
        if count == 0:
            return []

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=min(top_k, count),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []

        chunks = []
        if not results["documents"] or not results["documents"][0]:
            return chunks

        for text, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            similarity = 1.0 - (dist / 2.0)
            chunks.append(
                RetrievedChunk(
                    chunk_id=f"{meta['doc_id']}_chunk_{meta['chunk_index']}",
                    doc_id=meta["doc_id"],
                    filename=meta["filename"],
                    page_num=meta["page_num"],
                    chunk_index=meta["chunk_index"],
                    text=text,
                    relevance_score=round(similarity, 4),
                    metadata=meta,
                )
            )

        chunks.sort(key=lambda c: c.relevance_score, reverse=True)
        return chunks

    def delete_document(self, doc_id: str):
        try:
            self.collection.delete(where={"doc_id": doc_id})
        except Exception as e:
            logger.warning(f"Delete failed for {doc_id}: {e}")

    def list_indexed_docs(self) -> list:
        try:
            results = self.collection.get(include=["metadatas"])
            seen = {}
            for meta in results["metadatas"]:
                doc_id = meta.get("doc_id", "")
                if doc_id and doc_id not in seen:
                    seen[doc_id] = {
                        "doc_id": doc_id,
                        "filename": meta.get("filename", ""),
                        "doc_type": meta.get("doc_type", ""),
                    }
            return list(seen.values())
        except Exception as e:
            logger.warning(f"list_indexed_docs error: {e}")
            return []

    def _chunk_document(self, processed_doc) -> list:
        chunks = []
        chunk_index = 0

        for page in processed_doc.pages:
            text = page.cleaned_text.strip()
            if not text or page.confidence == "low":
                continue

            words = text.split()
            if len(words) <= CHUNK_SIZE:
                chunks.append(
                    {"index": chunk_index, "text": text, "page_num": page.page_num}
                )
                chunk_index += 1
            else:
                start = 0
                while start < len(words):
                    end = min(start + CHUNK_SIZE, len(words))
                    chunk_text = " ".join(words[start:end])
                    chunks.append(
                        {
                            "index": chunk_index,
                            "text": chunk_text,
                            "page_num": page.page_num,
                        }
                    )
                    chunk_index += 1
                    if end == len(words):
                        break
                    start += CHUNK_SIZE - CHUNK_OVERLAP

        structured = processed_doc.structured
        meta_chunk_parts = [
            f"Document type: {structured.document_type}",
            f"Parties: {', '.join(structured.parties)}" if structured.parties else "",
            f"Dates: {', '.join(structured.dates)}" if structured.dates else "",
            f"Case numbers: {', '.join(structured.case_numbers)}"
            if structured.case_numbers
            else "",
            f"Amounts: {', '.join(structured.amounts)}" if structured.amounts else "",
        ]
        meta_chunk = " | ".join(p for p in meta_chunk_parts if p)
        if meta_chunk:
            chunks.append(
                {"index": chunk_index, "text": meta_chunk, "page_num": 0}
            )

        return chunks

    def format_evidence_block(self, chunks: list) -> str:
        if not chunks:
            return "No relevant evidence retrieved."

        lines = []
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"[Evidence {i}] (File: {chunk.filename}, Page {chunk.page_num}, "
                f"Relevance: {chunk.relevance_score:.2f})\n{chunk.text}"
            )
        return "\n\n".join(lines)
