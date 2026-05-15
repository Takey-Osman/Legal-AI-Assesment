from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.document_processor import process_document
from src.draft_generator import generate_grounded_draft
from src.edit_learner import build_edit_guidance, save_edit
from src.evaluation import evaluate_output
from src.models import DocumentChunk
from src.retriever import TfidfRetriever


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the legal AI assessment pipeline.")
    parser.add_argument("--input", default="data/sample_legal_notice.txt", help="Path to PDF/image/text input")
    parser.add_argument("--task", default="notice-related summary", help="Drafting task")
    parser.add_argument("--query", default=None, help="Retrieval query")
    parser.add_argument("--simulate-edit", action="store_true", help="Save a simulated operator edit")
    args = parser.parse_args()

    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)

    processed = process_document(args.input, output_dir=output_dir)
    chunks = [DocumentChunk(**chunk) for chunk in processed["chunks"]]
    query = args.query or f"Generate a {args.task} from the document"

    retriever = TfidfRetriever(chunks)
    evidence = retriever.search(query, k=5)

    edit_memory = output_dir / "edit_memory.jsonl"
    guidance = build_edit_guidance(edit_memory)
    draft = generate_grounded_draft(args.task, processed["structured_fields"], evidence, guidance)

    (output_dir / "generated_draft.md").write_text(draft, encoding="utf-8")
    evaluation = evaluate_output(draft, evidence, processed["structured_fields"])
    (output_dir / "evaluation_results.json").write_text(json.dumps(evaluation, indent=2), encoding="utf-8")

    if args.simulate_edit:
        edited = draft.replace("# First-Pass Grounded Draft", "# Reviewed First-Pass Draft")
        edited += "\nOperator note: keep the summary concise and preserve evidence labels.\n"
        save_edit(draft, edited, edit_memory)

    print("Pipeline complete.")
    print(f"Draft written to: {output_dir / 'generated_draft.md'}")
    print(f"Evaluation written to: {output_dir / 'evaluation_results.json'}")


if __name__ == "__main__":
    main()
