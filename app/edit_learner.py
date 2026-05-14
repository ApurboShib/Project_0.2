import json
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List
from app.config import LLM_PROVIDER

logger = logging.getLogger(__name__)


@dataclass
class EditRecord:
    edit_id: str
    draft_id: str
    draft_type: str
    original_draft: str
    edited_draft: str
    extracted_rules: list
    timestamp: str
    operator_note: str = ""


class EditLearner:
    """
    Analyzes diffs between original and operator-edited drafts.
    Extracts transferable style/content rules using Claude.
    """

    MODEL = "llama-3.3-70b-versatile"  # GROQ free tier

    EXTRACTION_SYSTEM = """You are analyzing how a legal professional edited an AI-generated draft.
Your job is to extract REUSABLE style and content patterns from the edits.

Rules you extract should be:
- Generalizable (not specific to this one document)
- Actionable (tells future drafts what TO DO or NOT DO)
- Concise (one sentence each)

Examples of good rules:
- "Always include the contract execution date in the first paragraph"
- "Use 'the Company' instead of referring to party by full name after first mention"
- "Add a 'Next Steps' section at the end of internal memos"
- "Avoid passive voice in findings sections"
- "Include specific dollar amounts in the overview, not just relative references"

Output ONLY a JSON array of rule strings, nothing else.
Example: ["Rule 1", "Rule 2", "Rule 3"]
"""

    def __init__(self, client, style_store=None):
        self.client = client
        self.style_store = style_store

    def process_edit(
        self,
        edit_id: str,
        draft_id: str,
        draft_type: str,
        original: str,
        edited: str,
        operator_note: str = "",
    ) -> EditRecord:
        """
        Process an operator edit:
        1. Compute a meaningful diff summary
        2. Extract style rules via Claude
        3. Store rules for future use
        4. Return the edit record
        """
        if original.strip() == edited.strip():
            return EditRecord(
                edit_id=edit_id,
                draft_id=draft_id,
                draft_type=draft_type,
                original_draft=original,
                edited_draft=edited,
                extracted_rules=[],
                timestamp=datetime.utcnow().isoformat(),
                operator_note=operator_note or "No changes detected",
            )

        diff_summary = self._compute_diff_summary(original, edited)
        rules = []
        if self.client:
            rules = self._extract_rules(diff_summary, draft_type, operator_note)

        if self.style_store:
            self.style_store.upsert_style_rule(draft_type, "\n".join(rules))

        record = EditRecord(
            edit_id=edit_id,
            draft_id=draft_id,
            draft_type=draft_type,
            original_draft=original,
            edited_draft=edited,
            extracted_rules=rules,
            timestamp=datetime.utcnow().isoformat(),
            operator_note=operator_note,
        )
        return record

    def _compute_diff_summary(self, original: str, edited: str) -> str:
        """
        Produce a human-readable diff summary for the LLM.
        Uses line-level comparison to find additions and removals.
        """
        orig_lines = [l.strip() for l in original.split("\n") if l.strip()]
        edit_lines = [l.strip() for l in edited.split("\n") if l.strip()]

        orig_set = set(orig_lines)
        edit_set = set(edit_lines)

        removed = [f"- {l}" for l in orig_lines if l not in edit_set]
        added = [f"+ {l}" for l in edit_lines if l not in orig_set]

        parts = []
        if removed:
            parts.append("LINES REMOVED:\n" + "\n".join(removed[:20]))
        if added:
            parts.append("LINES ADDED:\n" + "\n".join(added[:20]))

        orig_wc = len(original.split())
        edit_wc = len(edited.split())
        parts.append(f"Word count: {orig_wc} → {edit_wc} ({edit_wc - orig_wc:+d})")

        return "\n\n".join(parts) if parts else "Minor whitespace/formatting changes only"

    def _extract_rules(
        self, diff_summary: str, draft_type: str, operator_note: str
    ) -> List[str]:
        """Ask Claude to extract reusable rules from the diff."""
        user_content = f"""Draft type: {draft_type}

DIFF BETWEEN ORIGINAL AND EDITED DRAFT:
{diff_summary}
"""
        if operator_note:
            user_content += f"\nOPERATOR'S NOTE ABOUT THE EDIT:\n{operator_note}"

        user_content += "\n\nExtract 2-5 reusable rules as a JSON array."

        try:
            if LLM_PROVIDER == "groq":
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": self.EXTRACTION_SYSTEM},
                        {"role": "user", "content": user_content}
                    ],
                    max_tokens=500,
                )
                raw = response.choices[0].message.content.strip()
            else:
                response = self.client.messages.create(
                    model=self.MODEL,
                    max_tokens=500,
                    system=self.EXTRACTION_SYSTEM,
                    messages=[{"role": "user", "content": user_content}],
                )
                raw = response.content[0].text.strip()
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            rules = json.loads(raw)
            if isinstance(rules, list):
                return [str(r) for r in rules if isinstance(r, str)]
        except Exception as e:
            logger.warning(f"Rule extraction failed: {e}")
        return []
