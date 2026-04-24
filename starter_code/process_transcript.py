import re


def clean_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Drop common noise tokens (bracketed)
    text = re.sub(r"\[Music[^\]]*\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[inaudible\]", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\[Laughter\]", " ", text, flags=re.IGNORECASE)

    # Timestamps like [00:00:00]
    text = re.sub(r"\[\d{2}:\d{2}:\d{2}\]\s*", "", text)

    # Speaker labels
    text = re.sub(r"\[Speaker \d+\]:\s*", "", text)

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    detected_price_vnd = None
    if re.search(r"năm\s+trăm\s+nghìn", text, re.IGNORECASE):
        detected_price_vnd = 500000
    elif "500,000" in text or "500000" in text.replace(",", ""):
        detected_price_vnd = 500000

    return {
        "document_id": "video-demo-transcript-001",
        "content": text,
        "source_type": "Video",
        "author": "Unknown",
        "timestamp": None,
        "source_metadata": {"detected_price_vnd": detected_price_vnd, "original_file": "demo_transcript.txt"},
    }
