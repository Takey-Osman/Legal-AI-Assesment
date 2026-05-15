# Legal Document Understanding and Grounded Draft Generator

This repository is a practical take-home assessment submission for an AI Engineer role. It processes messy legal-style documents, extracts usable text and structured fields, retrieves relevant evidence, generates grounded first-pass drafts, and captures operator edits to improve future drafts.

The goal is not to provide legal advice. The goal is to demonstrate document processing, grounded retrieval, evidence-backed drafting, and a simple improvement loop.

## What the system does

1. **Document processing**
   - Accepts PDF, image, TXT, and Markdown files.
   - Extracts native PDF text using PyMuPDF.
   - Attempts OCR for scanned/low-text PDF pages and image files using Tesseract OCR.
   - Marks unclear pages when extraction is not reliable.
   - Extracts simple structured fields such as document type, dates, reference number, parties, address/property, and amounts.

2. **Grounded retrieval**
   - Splits extracted text into chunks.
   - Builds an offline TF-IDF retrieval layer.
   - Retrieves the most relevant evidence chunks for the requested drafting task.
   - Shows evidence IDs, source file, page number, and retrieval score.

3. **Draft generation**
   - Generates a conservative first-pass legal-style draft.
   - Every evidence-based summary bullet includes an evidence citation such as `[E1: file, page 1]`.
   - The draft avoids unsupported legal conclusions.

4. **Improvement from operator edits**
   - Operators can edit the draft.
   - The system saves edit records in `outputs/edit_memory.jsonl`.
   - It analyzes reusable signals such as length change and added headings.
   - Future drafts reuse these signals as style guidance.

## Repository structure

```text
legal_ai_assessment/
├── app.py
├── cli.py
├── requirements.txt
├── README.md
├── architecture.md
├── assumptions_tradeoffs.md
├── evaluation.md
├── data/
│   ├── sample_legal_notice.txt
│   └── sample_operator_edit.txt
├── sample_outputs/
│   ├── sample_extracted_text.json
│   ├── sample_generated_draft.md
│   └── sample_evaluation_results.json
├── outputs/
│   └── .gitkeep
├── src/
│   ├── document_processor.py
│   ├── draft_generator.py
│   ├── edit_learner.py
│   ├── evaluation.py
│   ├── models.py
│   └── retriever.py
└── tests/
    └── test_basic_pipeline.py
```

## Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it:

```bash
# macOS/Linux
source .venv/bin/activate

# Windows
.venv\Scripts\activate
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Optional OCR system dependency

For OCR on scanned images/PDFs, install the Tesseract OCR engine.

- Ubuntu/Debian: `sudo apt-get install tesseract-ocr`
- macOS: `brew install tesseract`
- Windows: install Tesseract from the official Windows installer and add it to PATH.

The app still works for native PDFs and text files without system OCR.

## Run with Streamlit UI

```bash
streamlit run app.py
```

Then upload `data/sample_legal_notice.txt` or any legal-style PDF/image/text file.

## Run with CLI

```bash
python cli.py --input data/sample_legal_notice.txt --task "notice-related summary"
```

This creates:

```text
outputs/extracted_text.json
outputs/generated_draft.md
outputs/evaluation_results.json
```

To simulate an operator edit:

```bash
python cli.py --input data/sample_legal_notice.txt --simulate-edit
```

Then run again. The next generated draft will include learned style guidance from previous edits.

## Sample output excerpt

```markdown
# First-Pass Grounded Draft: Notice-Related Summary

## Document Snapshot
- Document type: Notice / legal communication
- Reference number: PSL-2026-047
- Dates found: 01 January 2025, 05 April 2026, 12 May 2026

## Grounded Summary
- This notice concerns unpaid rent under the tenancy agreement dated 01 January 2025... [E1: sample_legal_notice.txt]
```

## Evaluation approach

The sample evaluation checks:

- number of retrieved evidence chunks,
- whether generated draft citations match retrieved evidence IDs,
- whether important structured fields were extracted,
- manual-review notes for legal correctness and OCR reliability.

See `evaluation.md` and `sample_outputs/` for the sample run results.

## Known limitations

- TF-IDF retrieval is transparent and offline but weaker than embedding retrieval.
- Rule-based field extraction is easy to inspect but less robust than a trained NER model.
- OCR quality depends on scan quality and Tesseract installation.
- The generated draft is conservative and template-based. A production system could use an LLM with strict citation requirements.
- The edit learning loop is intentionally simple. It captures reusable style signals but does not fine-tune a model.

## Submission steps

1. Push this repository to GitHub.
2. Invite these collaborators:
   - `github.com/tsensei`
   - `github.com/abubakarsiddik31`
3. Email the GitHub repo link with a short self-introduction to the assessment contact.
