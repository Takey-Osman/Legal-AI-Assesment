from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

from .models import DocumentChunk


DATE_PATTERNS = [
    r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
    r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
]


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_text(path: str | Path) -> Tuple[str, List[Dict[str, Any]]]:
    """Extract text from PDF, image, or text files.

    PDF native text is extracted first. If a PDF page has very little text, OCR is attempted.
    OCR dependencies are optional so the app still runs in basic environments.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()

    if suffix in {".txt", ".md"}:
        text = _clean_text(file_path.read_text(encoding="utf-8", errors="ignore"))
        return text, [{"page": None, "method": "plain_text", "text": text}]

    if suffix == ".pdf":
        return _extract_pdf(file_path)

    if suffix in {".png", ".jpg", ".jpeg", ".tif", ".tiff"}:
        text = _ocr_image(file_path)
        return _clean_text(text), [{"page": 1, "method": "image_ocr", "text": _clean_text(text)}]

    raise ValueError(f"Unsupported file type: {suffix}")


def _extract_pdf(file_path: Path) -> Tuple[str, List[Dict[str, Any]]]:
    page_records: List[Dict[str, Any]] = []
    full_text_parts: List[str] = []

    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("PyMuPDF is required for PDF extraction. Install requirements.txt") from exc

    doc = fitz.open(str(file_path))
    for page_index, page in enumerate(doc):
        page_no = page_index + 1
        native_text = _clean_text(page.get_text("text"))
        method = "pdf_text"
        final_text = native_text

        # If the page seems scanned or mostly unreadable, attempt OCR.
        if len(native_text) < 80:
            ocr_text = _ocr_pdf_page(page)
            if len(ocr_text) > len(native_text):
                final_text = ocr_text
                method = "pdf_page_ocr"
            elif not native_text:
                final_text = "[UNCLEAR PAGE: OCR/text extraction produced little or no text]"
                method = "unclear"

        final_text = _clean_text(final_text)
        page_records.append({"page": page_no, "method": method, "text": final_text})
        full_text_parts.append(f"\n\n--- Page {page_no} ---\n{final_text}")

    return _clean_text("".join(full_text_parts)), page_records


def _ocr_pdf_page(page: Any) -> str:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return ""

    try:
        pix = page.get_pixmap(matrix=None, dpi=220)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return _clean_text(pytesseract.image_to_string(img))
    except Exception:
        return ""


def _ocr_image(file_path: Path) -> str:
    try:
        import pytesseract
        from PIL import Image
    except Exception as exc:
        raise RuntimeError(
            "Image OCR needs pillow and pytesseract. Also install the Tesseract OCR engine on your OS."
        ) from exc

    image = Image.open(file_path)
    return _clean_text(pytesseract.image_to_string(image))


def extract_structured_fields(text: str) -> Dict[str, Any]:
    """Lightweight field extraction for messy legal-style documents.

    This is intentionally transparent and rule-based for reviewability. It can be replaced
    by a trained NER model later.
    """
    fields: Dict[str, Any] = {}
    lower = text.lower()

    if "notice" in lower:
        fields["document_type"] = "Notice / legal communication"
    elif "agreement" in lower or "contract" in lower:
        fields["document_type"] = "Agreement / contract"
    elif "deed" in lower or "title" in lower:
        fields["document_type"] = "Title / deed record"
    else:
        fields["document_type"] = "Unknown legal-style document"

    dates: List[str] = []
    for pattern in DATE_PATTERNS:
        dates.extend(re.findall(pattern, text, flags=re.IGNORECASE))
    fields["dates_found"] = sorted(set(dates))

    case_match = re.search(r"(?:case|matter|file|ref(?:erence)?)\s*(?:no\.?|number|#)?\s*[:\-]?\s*([A-Z0-9\-/]{3,})", text, re.IGNORECASE)
    if case_match:
        fields["reference_number"] = case_match.group(1)

    amount_matches = re.findall(r"(?:BDT|USD|Tk\.?|\$)\s?\d[\d,]*(?:\.\d{1,2})?", text, flags=re.IGNORECASE)
    if amount_matches:
        fields["amounts_found"] = sorted(set(amount_matches))

    party_patterns = {
        "sender_or_claimant": r"(?:from|claimant|landlord|seller|plaintiff)\s*[:\-]\s*([^\n]+)",
        "recipient_or_respondent": r"(?:to|recipient|tenant|buyer|defendant)\s*[:\-]\s*([^\n]+)",
        "property_address": r"(?:property|premises|address)\s*[:\-]\s*([^\n]+)",
    }
    for key, pattern in party_patterns.items():
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            fields[key] = match.group(1).strip()

    unclear_count = len(re.findall(r"unclear|illegible|\[.*?unclear.*?\]", text, flags=re.IGNORECASE))
    fields["unclear_marker_count"] = unclear_count

    return fields


def chunk_pages(page_records: List[Dict[str, Any]], source_file: str, chunk_size: int = 900, overlap: int = 120) -> List[DocumentChunk]:
    chunks: List[DocumentChunk] = []
    safe_overlap = min(overlap, max(0, chunk_size - 1))

    for record in page_records:
        page = record.get("page")
        text = _clean_text(record.get("text", ""))
        if not text:
            continue
        start = 0
        chunk_index = 1
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end].strip()
            if chunk_text:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"p{page or 'x'}_c{chunk_index}",
                        source_file=source_file,
                        page=page,
                        text=chunk_text,
                    )
                )
            if end >= len(text):
                break
            start = end - safe_overlap
            chunk_index += 1
    return chunks


def process_document(path: str | Path, output_dir: str | Path | None = None) -> Dict[str, Any]:
    file_path = Path(path)
    text, page_records = extract_text(file_path)
    fields = extract_structured_fields(text)
    chunks = chunk_pages(page_records, source_file=file_path.name)

    result = {
        "source_file": file_path.name,
        "extracted_text": text,
        "structured_fields": fields,
        "pages": page_records,
        "chunks": [chunk.to_dict() for chunk in chunks],
    }

    if output_dir:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "extracted_text.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    return result
