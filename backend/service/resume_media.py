"""Resume file helpers: text extraction and vision-model image preparation."""

from __future__ import annotations

import base64

import fitz

MAX_PDF_PAGES = 5
MAX_PDF_TEXT_PAGES = 20
PDF_RENDER_DPI = 150

IMAGE_MIME_TYPES = {
    "png": "image/png",
    "jpg": "image/jpeg",
}


def pdf_bytes_to_text(
    pdf_bytes: bytes,
    *,
    max_pages: int = MAX_PDF_TEXT_PAGES,
) -> str:
    """Extract plain text from a PDF using the embedded text layer (no LLM)."""
    if not pdf_bytes:
        return ""

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if len(doc) == 0:
            return ""

        parts: list[str] = []
        for page_index in range(min(len(doc), max_pages)):
            page_text = doc.load_page(page_index).get_text().strip()
            if page_text:
                parts.append(page_text)
        return "\n\n".join(parts).strip()
    finally:
        doc.close()


def extract_resume_text(file_bytes: bytes, file_type: str) -> str:
    """Extract readable text from a resume file for Interview / read_resume."""
    if file_type == "pdf":
        try:
            return pdf_bytes_to_text(file_bytes)
        except Exception:
            return ""
    # Image resumes have no text layer; vision/OCR is handled at analysis time only.
    return ""


def pdf_bytes_to_png_pages(
    pdf_bytes: bytes,
    *,
    dpi: int = PDF_RENDER_DPI,
    max_pages: int = MAX_PDF_PAGES,
) -> list[bytes]:
    """Render PDF pages to PNG bytes for vision LLM input."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        if len(doc) == 0:
            raise ValueError("PDF has no pages")

        zoom = dpi / 72.0
        matrix = fitz.Matrix(zoom, zoom)
        pages: list[bytes] = []
        for page_index in range(min(len(doc), max_pages)):
            pixmap = doc.load_page(page_index).get_pixmap(matrix=matrix)
            pages.append(pixmap.tobytes("png"))
        return pages
    finally:
        doc.close()


def prepare_resume_images(file_path: str, file_type: str) -> list[tuple[str, str]]:
    """Return base64-encoded images with MIME types for LLM vision input."""
    with open(file_path, "rb") as handle:
        file_bytes = handle.read()

    if file_type == "pdf":
        png_pages = pdf_bytes_to_png_pages(file_bytes)
        return [
            (base64.b64encode(page).decode("utf-8"), "image/png")
            for page in png_pages
        ]

    mime_type = IMAGE_MIME_TYPES.get(file_type)
    if not mime_type:
        raise ValueError(f"Unsupported resume file type: {file_type}")

    file_b64 = base64.b64encode(file_bytes).decode("utf-8")
    return [(file_b64, mime_type)]
