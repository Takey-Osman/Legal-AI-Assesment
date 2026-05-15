# Architecture Overview

## Pipeline

```text
Input document
   ↓
Document Processor
   - native PDF text extraction
   - OCR fallback for scanned/low-text pages
   - text cleaning
   - unclear-page marking
   ↓
Structured Field Extractor
   - document type
   - dates
   - reference number
   - parties/address/amounts
   ↓
Chunker
   - page-aware text chunks
   - overlap to preserve context
   ↓
Retriever
   - TF-IDF vector index
   - top-k evidence retrieval
   - evidence ID + page + score
   ↓
Draft Generator
   - conservative legal-style draft
   - evidence citations attached to factual claims
   - missing/unclear information flagged
   ↓
Operator Edit Learner
   - saves original vs edited draft
   - extracts reusable signals
   - future draft style guidance
```

## Key design choices

### Processing layer

The processor first attempts native PDF extraction. This is faster and more accurate when the PDF contains embedded text. If a page has very little extracted text, the system attempts OCR. This is important because messy legal records may be scanned or partially illegible.

### Retrieval layer

The current version uses TF-IDF. This keeps the demo simple, deterministic, and fully offline. For a production version, this can be replaced with sentence-transformer embeddings and FAISS/ChromaDB.

### Grounded drafting

The draft generator is intentionally conservative. It only uses retrieved evidence and structured fields. Every evidence-based summary line includes a citation to the retrieved chunk. This makes it easy for a reviewer to inspect the source of each claim.

### Improvement loop

The system does more than save a diff. It records edit metadata and extracts reusable preferences such as shorter/longer output and headings that operators tend to add. The next draft includes this learned guidance.

## Production extensions

- Add document classification for different legal workflows.
- Use layout-aware OCR for tables, stamps, and handwritten notes.
- Replace TF-IDF with vector embeddings and hybrid search.
- Add a strict LLM prompt that requires citations for every claim.
- Add claim-level verification.
- Add user authentication and audit logs.
- Store documents, chunks, and edits in a database.
