from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List


@dataclass
class DocumentChunk:
    chunk_id: str
    source_file: str
    page: int | None
    text: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class RetrievedEvidence:
    evidence_id: str
    chunk_id: str
    source_file: str
    page: int | None
    score: float
    text: str

    def citation(self) -> str:
        page_part = f", page {self.page}" if self.page is not None else ""
        return f"[{self.evidence_id}: {self.source_file}{page_part}]"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
