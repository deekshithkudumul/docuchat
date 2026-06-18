"""
services/pdf_extractor.py — PDF text extraction using PyMuPDF
"""
import fitz
from io import BytesIO

def extract_text(pdf_bytes: bytes) -> str:
    doc = fitz.open(stream=BytesIO(pdf_bytes), filetype="pdf")
    pages = []
    for page in doc:
        pages.append(page.get_text())
    doc.close()
    return "\n".join(pages)
