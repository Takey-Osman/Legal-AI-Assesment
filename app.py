from __future__ import annotations

import json
import tempfile
from pathlib import Path

import streamlit as st

from src.document_processor import process_document
from src.draft_generator import generate_grounded_draft
from src.edit_learner import build_edit_guidance, save_edit
from src.models import DocumentChunk
from src.retriever import TfidfRetriever

OUTPUT_DIR = Path("outputs")
EDIT_MEMORY = OUTPUT_DIR / "edit_memory.jsonl"

st.set_page_config(page_title="Legal AI Assessment", layout="wide")
st.title("Legal Document Understanding and Grounded Draft Generator")
st.caption("Take-home assessment demo: process messy documents, retrieve evidence, draft grounded output, and learn from edits.")

uploaded = st.file_uploader("Upload a legal-style document", type=["pdf", "png", "jpg", "jpeg", "txt", "md"])
task = st.selectbox(
    "Draft type",
    ["case fact summary", "notice-related summary", "document checklist", "first-pass internal memo", "title review summary"],
)
custom_query = st.text_input("Retrieval query", value=f"Generate a {task} from this document")

if uploaded:
    suffix = Path(uploaded.name).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded.read())
        tmp_path = Path(tmp.name)

    with st.spinner("Processing document..."):
        result = process_document(tmp_path, output_dir=OUTPUT_DIR)
        result["source_file"] = uploaded.name

    st.success("Document processed")

    left, right = st.columns([1, 2])
    with left:
        st.subheader("Structured fields")
        st.json(result["structured_fields"])

    chunks = [DocumentChunk(**chunk) for chunk in result["chunks"]]
    retriever = TfidfRetriever(chunks)
    evidence = retriever.search(custom_query, k=5)
    edit_guidance = build_edit_guidance(EDIT_MEMORY)
    draft = generate_grounded_draft(task, result["structured_fields"], evidence, edit_guidance)

    with right:
        st.subheader("Generated grounded draft")
        st.markdown(draft)

    st.subheader("Retrieved evidence")
    for item in evidence:
        with st.expander(f"{item.evidence_id} | page {item.page} | score {item.score:.3f}"):
            st.write(item.text)

    st.subheader("Operator edit loop")
    edited = st.text_area("Edit the draft here, then save feedback", value=draft, height=350)
    if st.button("Save operator edit"):
        record = save_edit(draft, edited, EDIT_MEMORY)
        st.success("Edit saved. Future drafts will reuse the learned style signal.")
        st.json(record)

    with st.expander("Raw processed output"):
        st.json(result)
else:
    st.info("Upload a sample legal document to begin. You can test with data/sample_legal_notice.txt.")
