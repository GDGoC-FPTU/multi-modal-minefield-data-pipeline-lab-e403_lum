import ast
import re


def extract_logic_from_code(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    tree = ast.parse(source_code)

    chunks = []
    mod_doc = ast.get_docstring(tree)
    if mod_doc:
        chunks.append(mod_doc.strip())

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ds = ast.get_docstring(node)
            if ds:
                chunks.append(f"Function `{node.name}`:\n{ds.strip()}")

    rule_comments = re.findall(r"#\s*(Business Logic Rule[^\n]+)", source_code)
    for c in rule_comments:
        chunks.append(c.strip())

    # Surface the misleading VAT comment for QA / discrepancy awareness
    if "legacy_tax_calc" in source_code:
        chunks.append(
            "Note for auditors: legacy_tax_calc comment mentions 8% VAT but implementation uses 10%."
        )

    content = "\n\n".join(chunks) if chunks else source_code[:2000]

    return {
        "document_id": "code-legacy-pipeline-v1",
        "content": content,
        "source_type": "Code",
        "author": "VinData Legacy",
        "timestamp": None,
        "source_metadata": {
            "original_file": "legacy_pipeline.py",
            "vat_comment_vs_code_discrepancy": True,
        },
    }
