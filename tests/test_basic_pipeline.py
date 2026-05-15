from pathlib import Path

from src.document_processor import process_document
from src.draft_generator import generate_grounded_draft
from src.models import DocumentChunk
from src.retriever import TfidfRetriever


def test_basic_pipeline_sample_document():
    sample = Path("data/sample_legal_notice.txt")
    processed = process_document(sample)
    assert processed["structured_fields"]["reference_number"] == "PSL-2026-047"
    assert processed["chunks"]

    chunks = [DocumentChunk(**chunk) for chunk in processed["chunks"]]
    evidence = TfidfRetriever(chunks).search("notice unpaid rent", k=3)
    assert evidence

    draft = generate_grounded_draft("notice-related summary", processed["structured_fields"], evidence)
    assert "Grounded Summary" in draft
    assert "[E1:" in draft
