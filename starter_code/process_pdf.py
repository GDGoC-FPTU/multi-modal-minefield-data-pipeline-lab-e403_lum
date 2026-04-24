import json
import os
import time

import google.generativeai as genai
from dotenv import load_dotenv

try:
    from google.api_core import exceptions as google_api_exceptions
except ImportError:  # pragma: no cover
    google_api_exceptions = None

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))


def _is_rate_limit_error(exc: BaseException) -> bool:
    msg = str(exc).lower()
    if "429" in msg or "resource exhausted" in msg or "quota" in msg:
        return True
    if google_api_exceptions and isinstance(
        exc, (google_api_exceptions.ResourceExhausted, google_api_exceptions.TooManyRequests)
    ):
        return True
    return False


def _wait_until_active(pdf_file, timeout_s: float = 120.0):
    deadline = time.time() + timeout_s
    file_name = pdf_file.name
    while time.time() < deadline:
        current = genai.get_file(file_name)
        state_name = getattr(getattr(current, "state", None), "name", "") or ""
        if state_name == "ACTIVE":
            return current
        if state_name == "FAILED":
            raise RuntimeError("Gemini file upload/processing failed.")
        time.sleep(2)
    return genai.get_file(file_name)


def _generate_with_backoff(model, parts, max_attempts: int = 6):
    delay = 1.0
    last_err = None
    for attempt in range(max_attempts):
        try:
            return model.generate_content(parts)
        except Exception as e:  # noqa: BLE001
            last_err = e
            if _is_rate_limit_error(e) and attempt < max_attempts - 1:
                time.sleep(delay)
                delay = min(delay * 2, 60.0)
                continue
            raise
    if last_err:
        raise last_err
    return None


def extract_pdf_data(file_path):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key.strip() in ("", "your_api_key_here"):
        print("Warning: GEMINI_API_KEY missing or placeholder; skipping PDF extraction.")
        return None

    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.5-flash")

    print(f"Uploading {file_path} to Gemini...")
    try:
        pdf_file = genai.upload_file(path=file_path)
        pdf_file = _wait_until_active(pdf_file)
    except Exception as e:  # noqa: BLE001
        print(f"Failed to upload file to Gemini: {e}")
        return None

    prompt = """
Analyze this PDF. Extract: Title, Author, Main Topics (list), and a short description of any tables.

Respond with ONE JSON object only (no markdown fences), matching this shape:
{
  "document_id": "pdf-lecture-notes",
  "content": "A clear multi-sentence summary (at least 3 sentences) including title, author, main topics, and table overview.",
  "source_type": "PDF",
  "author": "Author name or Unknown",
  "timestamp": null,
  "source_metadata": {
    "original_file": "lecture_notes.pdf",
    "title": "",
    "main_topics": [],
    "tables": []
  }
}
"""

    print("Generating content from PDF using Gemini...")
    try:
        response = _generate_with_backoff(model, [pdf_file, prompt])
    except Exception as e:  # noqa: BLE001
        print(f"Gemini generate_content failed: {e}")
        return None

    if not response.candidates:
        print("Gemini returned no candidates for PDF.")
        return None

    content_text = (response.text or "").strip()
    if not content_text:
        print("Gemini returned empty text for PDF.")
        return None

    if content_text.startswith("```json"):
        content_text = content_text[7:]
    if content_text.startswith("```"):
        content_text = content_text[3:]
    if content_text.endswith("```"):
        content_text = content_text[:-3]

    try:
        extracted_data = json.loads(content_text.strip())
    except json.JSONDecodeError as e:
        print(f"Failed to parse Gemini JSON for PDF: {e}")
        return None

    return extracted_data
