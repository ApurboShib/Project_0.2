import re
from typing import List

from .storage import SQLiteStore


class StyleRuleStore:
    def __init__(self, store: SQLiteStore):
        self.store = store

    def get_rules(self, draft_type: str) -> list:
        return self.store.get_style_rules(draft_type)

    def learn_from_edit(self, draft_type: str, edited_text: str) -> List[str]:
        rules = self.extract_rules(edited_text)
        for rule in rules:
            self.store.upsert_style_rule(draft_type, rule)
        return rules

    def extract_rules(self, edited_text: str) -> List[str]:
        if not edited_text:
            return []

        lines = [line.strip() for line in edited_text.splitlines() if line.strip()]
        rules = []

        header_candidates = []
        for line in lines:
            if line.endswith(":"):
                header_candidates.append(line.rstrip(":").strip())
                continue
            if re.match(r"^[A-Z0-9 &/.\-]{4,}$", line):
                header_candidates.append(line.strip())

        for header in header_candidates[:8]:
            rules.append(f"Include section header: {header}")

        if any(line.startswith(("TO:", "FROM:", "RE:", "DATE:")) for line in lines):
            rules.append("Use a memo header block with TO/FROM/RE/DATE lines.")

        bullet_lines = [line for line in lines if line.lstrip().startswith(("-", "*"))]
        if len(bullet_lines) >= 4:
            rules.append("Prefer bullet points for itemized details.")

        if "not stated in documents" in edited_text.lower():
            rules.append("Use the phrase 'Not stated in documents' for missing information.")

        seen = set()
        unique_rules = []
        for rule in rules:
            if rule not in seen:
                unique_rules.append(rule)
                seen.add(rule)
        return unique_rules
