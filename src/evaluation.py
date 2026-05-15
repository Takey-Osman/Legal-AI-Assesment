from __future__ import annotations

import re
from typing import Dict, List

from .models import RetrievedEvidence


def evaluate_output(draft: str, evidence: List[RetrievedEvidence], structured_fields: Dict[str, object]) -> Dict[str, object]:
    """Small transparent evaluation for the sample run.

    This is not a legal-quality benchmark. It checks whether the demo output is grounded
    and whether extraction produced usable fields.
    """
    evidence_ids = {item.evidence_id for item in evidence}
    cited_ids = set(re.findall(r"\[(E\d+):", draft))
    grounded_citation_coverage = len(cited_ids & evidence_ids) / max(1, len(evidence_ids))

    important_fields = ["document_type", "dates_found", "reference_number"]
    field_presence = {
        key: bool(structured_fields.get(key)) for key in important_fields
    }

    return {
        "retrieved_evidence_count": len(evidence),
        "cited_evidence_ids": sorted(cited_ids),
        "grounded_citation_coverage": round(grounded_citation_coverage, 3),
        "field_presence": field_presence,
        "notes": "Manual review is still required for legal correctness and OCR errors.",
    }
