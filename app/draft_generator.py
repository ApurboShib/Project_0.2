import logging
from dataclasses import dataclass, field
from app.config import LLM_PROVIDER

logger = logging.getLogger(__name__)

DRAFT_TYPES = {
    "case_fact_summary": "Case Fact Summary",
    "internal_memo": "Internal Memo",
    "notice_summary": "Notice-Related Summary",
    "document_checklist": "Document Checklist",
    "title_review": "Title Review Summary",
}

SYSTEM_PROMPT = """You are a legal document analyst at Pearson Specter Litt.
Your task is to produce a grounded draft based ONLY on the evidence passages provided.

Critical rules:
1. Every claim you make MUST be supported by the evidence passages below.
2. If information is not in the evidence, say "Not stated in documents" -- never invent facts.
3. For each major point, cite the evidence number (e.g. [Evidence 2]).
4. Flag any gaps or ambiguities in the source documents.
5. Structure your output clearly with labeled sections.
6. Maintain a professional legal tone throughout.
"""


@dataclass
class DraftResult:
    draft_id: str
    doc_ids: list
    draft_type: str
    draft_type_label: str
    title: str
    content: str
    evidence_used: list
    word_count: int
    model_used: str
    generation_notes: list = field(default_factory=list)
    style_rules_applied: list = field(default_factory=list)

    def to_dict(self):
        return {
            "draft_id": self.draft_id,
            "doc_ids": self.doc_ids,
            "draft_type": self.draft_type,
            "draft_type_label": self.draft_type_label,
            "title": self.title,
            "content": self.content,
            "evidence_used": self.evidence_used,
            "word_count": self.word_count,
            "model_used": self.model_used,
            "generation_notes": self.generation_notes,
            "style_rules_applied": self.style_rules_applied,
        }


class DraftGenerator:
    # GROQ models (free, very fast)
    MODEL = "mixtral-8x7b-32768"  # Free tier for GROQ
    GEMINI_MODEL = "gemini-pro"
    CLAUDE_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, client, style_store=None):
        self.client = client
        self.style_store = style_store

    def generate(
        self,
        draft_type: str,
        retrieved_chunks: list,
        doc_metadata: dict,
        draft_id: str,
        custom_instructions: str = "",
    ) -> DraftResult:
        if draft_type not in DRAFT_TYPES:
            raise ValueError(
                f"Unknown draft type: {draft_type}. Choose from: {list(DRAFT_TYPES)}"
            )
        if not self.client:
            raise ValueError("LLM client not configured.")

        style_rules = []
        style_rules_text = ""
        if self.style_store:
            style_rules = self.style_store.get_rules(draft_type)
            if style_rules:
                style_rules_text = self._format_style_rules(style_rules)

        evidence_block = self._format_evidence(retrieved_chunks)

        user_prompt = self._build_prompt(
            draft_type=draft_type,
            evidence_block=evidence_block,
            doc_metadata=doc_metadata,
            style_rules_text=style_rules_text,
            custom_instructions=custom_instructions,
        )

        response = self.client.messages.create(
            model=self.MODEL,
            max_tokens=3000,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )

        draft_content = response.content[0].text
        word_count = len(draft_content.split())

        doc_names = doc_metadata.get("filenames", ["document"])
        title = f"{DRAFT_TYPES[draft_type]}: {', '.join(doc_names[:2])}"

        return DraftResult(
            draft_id=draft_id,
            doc_ids=doc_metadata.get("doc_ids", []),
            draft_type=draft_type,
            draft_type_label=DRAFT_TYPES[draft_type],
            title=title,
            content=draft_content,
            evidence_used=[
                {
                    "chunk_id": c.chunk_id,
                    "filename": c.filename,
                    "page_num": c.page_num,
                    "text": c.text[:300] + "..." if len(c.text) > 300 else c.text,
                    "relevance_score": c.relevance_score,
                }
                for c in retrieved_chunks
            ],
            word_count=word_count,
            model_used=self.MODEL,
            style_rules_applied=[r["rule_text"] for r in style_rules],
            generation_notes=[
                f"Evidence chunks used: {len(retrieved_chunks)}",
                f"Style rules applied: {len(style_rules)}",
                f"Custom instructions: {'yes' if custom_instructions else 'none'}",
            ],
        )

    def _build_prompt(
        self,
        draft_type: str,
        evidence_block: str,
        doc_metadata: dict,
        style_rules_text: str,
        custom_instructions: str,
    ) -> str:
        type_label = DRAFT_TYPES[draft_type]
        doc_type = doc_metadata.get("doc_type", "legal document")
        filenames = ", ".join(doc_metadata.get("filenames", ["document"]))

        type_instructions = self._get_type_instructions(draft_type)

        prompt = f"""Please produce a {type_label} for the following legal document(s): {filenames}
Document type detected: {doc_type}

EVIDENCE FROM SOURCE DOCUMENTS:
{evidence_block}

DRAFT TYPE INSTRUCTIONS:
{type_instructions}
"""

        if style_rules_text:
            prompt += (
                "\nOPERATOR STYLE PREFERENCES (apply these based on past edits):\n"
                f"{style_rules_text}\n"
            )

        if custom_instructions:
            prompt += f"\nADDITIONAL INSTRUCTIONS:\n{custom_instructions}\n"

        prompt += "\nProduce the draft now. Cite evidence numbers for each major claim. Flag any gaps."
        return prompt

    def _get_type_instructions(self, draft_type: str) -> str:
        instructions = {
            "case_fact_summary": (
                "Produce a Case Fact Summary with these sections:\n"
                "1. PARTIES -- who is involved\n"
                "2. KEY FACTS -- what happened, in chronological order if possible\n"
                "3. LEGAL ISSUES -- what legal questions are raised\n"
                "4. RELEVANT DATES -- key timeline entries\n"
                "5. MONETARY AMOUNTS -- any dollar figures mentioned\n"
                "6. GAPS & AMBIGUITIES -- what information is missing or unclear"
            ),
            "internal_memo": (
                "Produce an Internal Memo with:\n"
                "TO: [Senior Partner / Supervising Attorney]\n"
                "FROM: [AI Document Review]\n"
                "RE: [Document name and matter]\n"
                "DATE: [Today]\n"
                "Then sections: OVERVIEW, KEY FINDINGS, ISSUES TO FLAG, RECOMMENDED NEXT STEPS"
            ),
            "notice_summary": (
                "Produce a Notice-Related Summary with sections:\n"
                "1. NOTICE TYPE & PURPOSE\n"
                "2. NOTIFYING PARTY\n"
                "3. RECIPIENT(S)\n"
                "4. KEY OBLIGATIONS OR DEADLINES\n"
                "5. CONSEQUENCES OF NON-COMPLIANCE\n"
                "6. RELEVANT DATES"
            ),
            "document_checklist": (
                "Produce a Document Checklist showing:\n"
                "For each document or requirement mentioned in the source:\n"
                "- ITEM: what is required\n"
                "- STATUS: present in documents / missing / unclear\n"
                "- NOTES: any caveats\n"
                "End with a MISSING ITEMS section."
            ),
            "title_review": (
                "Produce a Title Review Summary with sections:\n"
                "1. DOCUMENT OVERVIEW\n"
                "2. PARTIES & SIGNATORIES\n"
                "3. KEY TERMS & CONDITIONS\n"
                "4. DATES & DEADLINES\n"
                "5. FINANCIAL TERMS\n"
                "6. RISKS & RED FLAGS\n"
                "7. REVIEWER NOTES"
            ),
        }
        return instructions.get(
            draft_type, "Produce a well-structured legal draft based on the evidence."
        )

    def _format_evidence(self, chunks: list) -> str:
        if not chunks:
            return "No evidence retrieved. Cannot produce a grounded draft."
        lines = []
        for i, chunk in enumerate(chunks, 1):
            lines.append(
                f"[Evidence {i}]\n"
                f"Source: {chunk.filename} | Page {chunk.page_num} | "
                f"Relevance: {chunk.relevance_score:.2f}\n"
                f"{chunk.text}"
            )
        return "\n\n".join(lines)

    def _format_style_rules(self, rules: list) -> str:
        lines = []
        for r in rules:
            freq = r.get("frequency", 1)
            lines.append(f"- {r['rule_text']} (seen {freq} time(s))")
        return "\n".join(lines)
