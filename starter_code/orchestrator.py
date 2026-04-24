import json
import os
import time

from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_ROOT, "raw_data")

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from schema import UnifiedDocument
from process_pdf import extract_pdf_data
from process_transcript import clean_transcript
from process_html import parse_html_catalog
from process_csv import process_sales_csv
from process_legacy_code import extract_logic_from_code
from quality_check import run_quality_gate


def _to_serializable(doc: UnifiedDocument):
    if hasattr(doc, "model_dump"):
        return doc.model_dump(mode="json")
    return doc.dict()


def _validate_unified(raw):
    if hasattr(UnifiedDocument, "model_validate"):
        return UnifiedDocument.model_validate(raw)
    return UnifiedDocument.parse_obj(raw)


def _ingest_dict(final_kb, raw):
    if raw is None:
        return
    if isinstance(raw, list):
        for item in raw:
            _ingest_dict(final_kb, item)
        return
    try:
        doc = _validate_unified(raw)
    except Exception as e:  # noqa: BLE001
        print(f"Schema validation failed for one document: {e}")
        return

    payload = _to_serializable(doc)
    if run_quality_gate(payload):
        final_kb.append(payload)
    else:
        print(f"Quality gate rejected document_id={payload.get('document_id')}")


def main():
    start_time = time.time()
    final_kb = []

    pdf_path = os.path.join(RAW_DATA_DIR, "lecture_notes.pdf")
    trans_path = os.path.join(RAW_DATA_DIR, "demo_transcript.txt")
    html_path = os.path.join(RAW_DATA_DIR, "product_catalog.html")
    csv_path = os.path.join(RAW_DATA_DIR, "sales_records.csv")
    code_path = os.path.join(RAW_DATA_DIR, "legacy_pipeline.py")

    output_path = os.path.join(PROJECT_ROOT, "processed_knowledge_base.json")

    _ingest_dict(final_kb, extract_pdf_data(pdf_path))
    _ingest_dict(final_kb, clean_transcript(trans_path))
    _ingest_dict(final_kb, parse_html_catalog(html_path))
    _ingest_dict(final_kb, process_sales_csv(csv_path))
    _ingest_dict(final_kb, extract_logic_from_code(code_path))

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_kb, f, ensure_ascii=False, indent=2)

    end_time = time.time()
    print(f"Pipeline finished in {end_time - start_time:.2f} seconds.")
    print(f"Total valid documents stored: {len(final_kb)}")
    print(f"Wrote {output_path}")


if __name__ == "__main__":
    main()
