"""Tests for resume media conversion helpers."""

from __future__ import annotations

import base64

import fitz
import pytest

from service.resume_media import (
    extract_resume_text,
    pdf_bytes_to_png_pages,
    pdf_bytes_to_text,
    prepare_resume_images,
)


def make_pdf_bytes(text: str = "Resume content") -> bytes:
    doc = fitz.open()
    try:
        page = doc.new_page()
        page.insert_text((72, 72), text)
        return doc.tobytes()
    finally:
        doc.close()


class TestPdfBytesToText:
    def test_extracts_embedded_text(self) -> None:
        text = pdf_bytes_to_text(make_pdf_bytes("Jane Doe Backend Engineer"))
        assert "Jane Doe" in text
        assert "Backend Engineer" in text

    def test_empty_bytes_returns_empty_string(self) -> None:
        assert pdf_bytes_to_text(b"") == ""


class TestExtractResumeText:
    def test_pdf_returns_text(self) -> None:
        pdf_bytes = make_pdf_bytes("Hello Resume")
        assert "Hello Resume" in extract_resume_text(pdf_bytes, "pdf")

    def test_image_returns_empty(self) -> None:
        assert extract_resume_text(b"\x89PNG", "png") == ""


class TestPdfBytesToPngPages:
    def test_renders_pdf_pages_to_png(self) -> None:
        png_pages = pdf_bytes_to_png_pages(make_pdf_bytes())

        assert len(png_pages) == 1
        assert png_pages[0].startswith(b"\x89PNG\r\n\x1a\n")

    def test_rejects_empty_pdf(self) -> None:
        with pytest.raises(Exception):
            pdf_bytes_to_png_pages(b"")


class TestPrepareResumeImages:
    def test_pdf_is_converted_to_png(self, tmp_path) -> None:
        pdf_path = tmp_path / "resume.pdf"
        pdf_path.write_bytes(make_pdf_bytes())

        images = prepare_resume_images(str(pdf_path), "pdf")

        assert len(images) == 1
        mime_type = images[0][1]
        png_bytes = base64.b64decode(images[0][0])
        assert mime_type == "image/png"
        assert png_bytes.startswith(b"\x89PNG\r\n\x1a\n")

    def test_png_is_passed_through(self, tmp_path) -> None:
        png_path = tmp_path / "resume.png"
        png_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")

        images = prepare_resume_images(str(png_path), "png")

        assert images == [(base64.b64encode(png_path.read_bytes()).decode("utf-8"), "image/png")]
