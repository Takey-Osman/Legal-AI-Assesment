from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _extract_headings(text: str) -> List[str]:
    return [line.strip("# ").strip() for line in text.splitlines() if line.startswith("#")]


def _sentence_count(text: str) -> int:
    return max(1, len(re.findall(r"[.!?]", text)))


def analyze_edit(original: str, edited: str) -> Dict[str, object]:
    original_len = max(1, len(original))
    edited_len = len(edited)
    original_headings = set(_extract_headings(original))
    edited_headings = set(_extract_headings(edited))

    added_headings = sorted(edited_headings - original_headings)
    removed_headings = sorted(original_headings - edited_headings)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "similarity": round(similarity(original, edited), 3),
        "length_ratio_edited_to_original": round(edited_len / original_len, 3),
        "original_sentence_count": _sentence_count(original),
        "edited_sentence_count": _sentence_count(edited),
        "added_headings": added_headings,
        "removed_headings": removed_headings,
        "original_excerpt": original[:600],
        "edited_excerpt": edited[:600],
    }


def save_edit(original: str, edited: str, memory_path: str | Path) -> Dict[str, object]:
    path = Path(memory_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    record = analyze_edit(original, edited)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record


def load_edit_records(memory_path: str | Path) -> List[Dict[str, object]]:
    path = Path(memory_path)
    if not path.exists():
        return []
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            records.append(json.loads(line))
    return records


def build_edit_guidance(memory_path: str | Path) -> str:
    records = load_edit_records(memory_path)
    if not records:
        return ""

    avg_ratio = sum(float(r["length_ratio_edited_to_original"]) for r in records) / len(records)
    added_headings: List[str] = []
    for record in records:
        added_headings.extend(record.get("added_headings", []))

    guidance = []
    if avg_ratio < 0.85:
        guidance.append("Operators usually shorten drafts. Keep future drafts more concise.")
    elif avg_ratio > 1.15:
        guidance.append("Operators usually expand drafts. Include more context in future drafts.")
    else:
        guidance.append("Operators usually keep draft length similar. Preserve concise structure.")

    if added_headings:
        common = sorted(set(added_headings))[:5]
        guidance.append("Operators often add these headings: " + ", ".join(common) + ".")

    guidance.append("Keep citations/evidence labels attached to factual claims.")
    return " ".join(guidance)
