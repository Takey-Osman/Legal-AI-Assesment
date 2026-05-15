# Assumptions and Tradeoffs

## Assumptions

- The system is evaluated as an engineering prototype, not a legal advice tool.
- Sample or synthetic documents are acceptable for demonstration.
- Some input documents may be scanned, noisy, incomplete, or partly illegible.
- Operator edits are valuable even if they are not enough for model fine-tuning.
- Grounding and inspectability are more important than polished UI.

## Tradeoffs

### TF-IDF instead of embedding search

TF-IDF is used because it is easy to run offline and simple to inspect. The tradeoff is that semantic matching is weaker than embedding-based retrieval.

### Rule-based field extraction instead of ML NER

Regex/rule-based extraction is transparent and easy to debug. The tradeoff is lower recall on unusual document formats.

### Template-based generation instead of free-form LLM output

The generator is conservative and avoids unsupported assumptions. The tradeoff is that the draft may sound less natural than a strong LLM-generated memo.

### Simple edit learning instead of fine-tuning

The edit learner captures reusable patterns such as preferred length and headings. This is practical for a take-home assessment. The tradeoff is that it does not deeply learn legal reasoning or language style.

## Error handling

- Unsupported file types raise a clear error.
- Low-text PDF pages trigger OCR when possible.
- If OCR/text extraction fails, unclear content is marked for human review.
- Draft output explicitly flags missing reference numbers, missing dates, or unclear text.
