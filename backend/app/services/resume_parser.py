"""
Plain-text extraction from uploaded resume files. Only PDF and DOCX are
supported — legacy binary .doc requires a system-level converter
(antiword/LibreOffice headless) that this project intentionally avoids,
so callers should reject .doc uploads before reaching here.
"""
from io import BytesIO

import docx
from pypdf import PdfReader


class ResumeParseError(Exception):
    """Raised when the file type is unsupported or no text could be extracted."""


def extract_text(file_bytes: bytes, filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    try:
        if ext == "pdf":
            text = _extract_pdf(file_bytes)
        elif ext == "docx":
            text = _extract_docx(file_bytes)
        else:
            raise ResumeParseError("Unsupported file type — upload a PDF or DOCX resume.")
    except ResumeParseError:
        raise
    except Exception as exc:
        raise ResumeParseError("This file looks corrupted or unreadable — please re-export it and try again.") from exc

    text = text.strip()
    if not text:
        raise ResumeParseError("Could not read text from this file.")
    return text


def _extract_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            pages.append(page_text)
    return "\n".join(pages)


def _extract_docx(file_bytes: bytes) -> str:
    document = docx.Document(BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs if p.text]
    return "\n".join(paragraphs)
