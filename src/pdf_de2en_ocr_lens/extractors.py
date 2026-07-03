from __future__ import annotations

import os
from pathlib import Path

from .models import Segment


class MissingDependencyError(RuntimeError):
    """Raised when an optional runtime dependency is required but missing."""


def extract_native_text(pdf_path: Path) -> list[Segment]:
    """Extract selectable PDF text with page and bounding-box metadata."""
    try:
        import fitz
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise MissingDependencyError("PyMuPDF is required for PDF extraction.") from exc

    segments: list[Segment] = []
    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            for block in page.get_text("blocks"):
                x0, y0, x1, y1, text, *_ = block
                cleaned = normalize_text(text)
                if cleaned:
                    segments.append(
                        Segment(
                            page=page_index,
                            source="native",
                            text=cleaned,
                            bbox=(float(x0), float(y0), float(x1), float(y1)),
                        )
                    )
    return segments


def extract_ocr_text(
    pdf_path: Path,
    dpi: int = 220,
    tesseract_lang: str = "deu+eng",
    min_confidence: float = 45.0,
    tesseract_cmd: str | None = None,
    tessdata_dir: str | None = None,
) -> list[Segment]:
    """Render each page and OCR the full image, including diagram labels."""
    try:
        import fitz
        import pytesseract
        from pytesseract import Output
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise MissingDependencyError(
            "OCR requires PyMuPDF and pytesseract. Install with `pip install .[ocr]` "
            "and install the Tesseract binary with German language data."
        ) from exc

    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    if tessdata_dir:
        os.environ["TESSDATA_PREFIX"] = tessdata_dir

    segments: list[Segment] = []
    scale = dpi / 72
    matrix = fitz.Matrix(scale, scale)

    with fitz.open(pdf_path) as document:
        for page_index, page in enumerate(document, start=1):
            pixmap = page.get_pixmap(matrix=matrix, alpha=False)
            image = pixmap_to_pillow(pixmap)
            data = pytesseract.image_to_data(
                image,
                lang=tesseract_lang,
                output_type=Output.DICT,
                config="--psm 6",
            )
            segments.extend(group_ocr_words(data, page_index, scale, min_confidence))

    return segments


def pixmap_to_pillow(pixmap):
    from PIL import Image

    mode = "RGB" if pixmap.n < 4 else "RGBA"
    return Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)


def group_ocr_words(data: dict[str, list], page: int, scale: float, min_confidence: float) -> list[Segment]:
    grouped: dict[tuple[int, int, int], list[tuple[str, float, tuple[float, float, float, float]]]] = {}
    count = len(data.get("text", []))

    for index in range(count):
        text = normalize_text(data["text"][index])
        if not text:
            continue
        try:
            confidence = float(data["conf"][index])
        except ValueError:
            confidence = -1.0
        if confidence < min_confidence:
            continue

        key = (
            int(data.get("block_num", [0])[index]),
            int(data.get("par_num", [0])[index]),
            int(data.get("line_num", [0])[index]),
        )
        left = float(data["left"][index]) / scale
        top = float(data["top"][index]) / scale
        width = float(data["width"][index]) / scale
        height = float(data["height"][index]) / scale
        grouped.setdefault(key, []).append((text, confidence, (left, top, left + width, top + height)))

    segments: list[Segment] = []
    for words in grouped.values():
        text = normalize_text(" ".join(word for word, _, _ in words))
        if not text:
            continue
        confidences = [confidence for _, confidence, _ in words]
        boxes = [box for _, _, box in words]
        x0 = min(box[0] for box in boxes)
        y0 = min(box[1] for box in boxes)
        x1 = max(box[2] for box in boxes)
        y1 = max(box[3] for box in boxes)
        segments.append(
            Segment(
                page=page,
                source="ocr",
                text=text,
                bbox=(x0, y0, x1, y1),
                confidence=round(sum(confidences) / len(confidences), 2),
            )
        )
    return segments


def normalize_text(text: str) -> str:
    return " ".join(text.replace("\x00", " ").split())
