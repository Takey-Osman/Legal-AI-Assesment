# Evaluation Approach and Results

## What is evaluated

The prototype includes a lightweight evaluation script in `src/evaluation.py`. It checks the sample output for:

1. **Evidence retrieval count**  
   Confirms that the retrieval layer returns evidence chunks for the drafting task.

2. **Grounding / citation coverage**  
   Checks whether evidence IDs used in the draft match the evidence IDs retrieved by the retriever.

3. **Structured field presence**  
   Checks whether important fields such as document type, dates, and reference number were extracted.

4. **Human-review warning**  
   Confirms that the system acknowledges OCR uncertainty and legal-review limitations.

## Sample run

Command:

```bash
python cli.py --input data/sample_legal_notice.txt --task "notice-related summary"
```

Expected output files:

```text
outputs/extracted_text.json
outputs/generated_draft.md
outputs/evaluation_results.json
```

Expected evaluation result shape:

```json
{
  "retrieved_evidence_count": 1,
  "cited_evidence_ids": ["E1"],
  "grounded_citation_coverage": 1.0,
  "field_presence": {
    "document_type": true,
    "dates_found": true,
    "reference_number": true
  },
  "notes": "Manual review is still required for legal correctness and OCR errors."
}
```

## Manual evaluation checklist

A reviewer should inspect:

- whether extracted text is usable,
- whether unclear content is marked,
- whether retrieved evidence is relevant to the drafting task,
- whether generated claims are supported by retrieved evidence,
- whether operator edits are saved and reused in later drafts.

## Limitations of the evaluation

This evaluation does not measure legal correctness. It only checks engineering behavior related to extraction, grounding, and edit reuse.
