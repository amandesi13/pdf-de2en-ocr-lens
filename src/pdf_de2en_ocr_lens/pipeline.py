from __future__ import annotations

from pathlib import Path

from .extractors import extract_native_text, extract_ocr_text
from .models import Segment, TranslatedSegment
from .output import write_outputs
from .translators import Translator


def convert_pdf(
    pdf_path: Path,
    output_dir: Path,
    translator: Translator,
    enable_ocr: bool = True,
    tesseract_lang: str = "deu+eng",
    min_confidence: float = 45.0,
    tesseract_cmd: str | None = None,
    tessdata_dir: str | None = None,
) -> list[TranslatedSegment]:
    pdf_path = pdf_path.expanduser().resolve()
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    segments = extract_native_text(pdf_path)
    if enable_ocr:
        segments.extend(
            extract_ocr_text(
                pdf_path,
                tesseract_lang=tesseract_lang,
                min_confidence=min_confidence,
                tesseract_cmd=tesseract_cmd,
                tessdata_dir=tessdata_dir,
            )
        )

    segments = dedupe_segments(segments)
    translated_texts = translator.translate_many([segment.text for segment in segments])
    translated_segments = [
        TranslatedSegment(
            page=segment.page,
            source=segment.source,
            original=segment.text,
            translated=translated,
            bbox=segment.bbox,
            confidence=segment.confidence,
        )
        for segment, translated in zip(segments, translated_texts)
    ]
    write_outputs(translated_segments, output_dir, pdf_path, translator.name)
    return translated_segments


def dedupe_segments(segments: list[Segment]) -> list[Segment]:
    """Remove exact duplicate text blocks while preserving OCR-only diagram labels."""
    seen: set[tuple[int, str]] = set()
    unique: list[Segment] = []
    for segment in sorted(segments, key=lambda item: (item.page, 0 if item.source == "native" else 1)):
        key = (segment.page, segment.text.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(segment)
    return unique
