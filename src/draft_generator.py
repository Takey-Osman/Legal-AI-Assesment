from __future__ import annotations

import re
from typing import Dict, List

from .models import RetrievedEvidence


def _shorten(text: str, max_chars: int = 420) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def generate_grounded_draft(
    task: str,
    structured_fields: Dict[str, object],
    evidence: List[RetrievedEvidence],
    edit_guidance: str | None = None,
) -> str:
    """Generate a conservative legal-style first draft using only retrieved evidence.

    This avoids unsupported assumptions by quoting/paraphrasing only available evidence.
    For a production version, replace this with an LLM call that receives the evidence list
    and is instructed to cite every claim.
    """
    doc_type = structured_fields.get("document_type", "Unknown")
    dates = structured_fields.get("dates_found", []) or []
    ref = structured_fields.get("reference_number", "Not found")
    unclear = structured_fields.get("unclear_marker_count", 0)

    lines: List[str] = []
    lines.append(f"# First-Pass Grounded Draft: {task.title()}")
    lines.append("")
    lines.append("## Document Snapshot")
    lines.append(f"- Document type: {doc_type}")
    lines.append(f"- Reference number: {ref}")
    lines.append(f"- Dates found: {', '.join(dates) if dates else 'No clear dates found'}")
    lines.append(f"- Unclear/illegible markers: {unclear}")

    known_fields = [
        ("Sender / claimant", structured_fields.get("sender_or_claimant")),
        ("Recipient / respondent", structured_fields.get("recipient_or_respondent")),
        ("Property / address", structured_fields.get("property_address")),
        ("Amounts found", ", ".join(structured_fields.get("amounts_found", []) or [])),
    ]
    for label, value in known_fields:
        if value:
            lines.append(f"- {label}: {value}")

    lines.append("")
    lines.append("## Grounded Summary")
    if not evidence:
        lines.append("No relevant evidence was retrieved, so no substantive draft is generated.")
    else:
        for item in evidence:
            lines.append(f"- { _shorten(item.text) } {item.citation()}")

    lines.append("")
    lines.append("## Issues / Missing Information")
    if unclear:
        lines.append("- Some content appears unclear or illegible. Human review is recommended before relying on this draft.")
    if not dates:
        lines.append("- No reliable date was extracted from the document.")
    if ref == "Not found":
        lines.append("- No clear reference/case/file number was extracted.")
    if evidence:
        lines.append("- The draft is limited to retrieved evidence and does not infer legal conclusions beyond the source text.")

    if edit_guidance:
        lines.append("")
        lines.append("## Style Guidance Reused From Prior Operator Edits")
        lines.append(edit_guidance)

    lines.append("")
    lines.append("## Evidence Index")
    for item in evidence:
        lines.append(f"- {item.evidence_id}: {item.source_file}, page {item.page}, score {item.score:.3f}")

    return "\n".join(lines).strip() + "\n"
