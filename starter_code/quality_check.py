import re


_TOXIC_SUBSTRINGS = (
    "null pointer exception",
    "stack trace:",
    "segmentation fault",
)


def run_quality_gate(document_dict):
    content = document_dict.get("content") or ""
    if len(content) < 20:
        return False

    lower = content.lower()
    for toxic in _TOXIC_SUBSTRINGS:
        if toxic in lower:
            return False

    meta = document_dict.get("source_metadata") or {}
    if document_dict.get("source_type") == "Code" and meta.get("vat_comment_vs_code_discrepancy"):
        # Lab: flag misleading VAT note — keep document but ensure it is explicit in content
        if "8%" not in content or "10%" not in content:
            return False

    return True
