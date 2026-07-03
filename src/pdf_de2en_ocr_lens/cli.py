from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .extractors import MissingDependencyError
from .pipeline import convert_pdf
from .translators import TranslationError, build_translator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pdf-de2en",
        description="Convert German PDFs to English, including OCR text from diagrams and graphics.",
    )
    parser.add_argument("pdf", type=Path, help="German PDF to convert.")
    parser.add_argument("-o", "--output", type=Path, default=Path("translation_output"), help="Output directory.")
    parser.add_argument(
        "--translator",
        choices=["passthrough", "demo", "deepl", "argos"],
        default="demo",
        help="Translation backend. Use DeepL for production quality.",
    )
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR over rendered pages.")
    parser.add_argument("--tesseract-lang", default="deu+eng", help="Tesseract language pack, e.g. deu+eng.")
    parser.add_argument("--tesseract-cmd", default=None, help="Path to tesseract executable if it is not on PATH.")
    parser.add_argument("--tessdata-dir", default=None, help="Directory containing .traineddata files.")
    parser.add_argument("--min-confidence", type=float, default=45.0, help="Minimum OCR confidence.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        translator = build_translator(args.translator)
        segments = convert_pdf(
            pdf_path=args.pdf,
            output_dir=args.output,
            translator=translator,
            enable_ocr=not args.no_ocr,
            tesseract_lang=args.tesseract_lang,
            min_confidence=args.min_confidence,
            tesseract_cmd=args.tesseract_cmd,
            tessdata_dir=args.tessdata_dir,
        )
    except (FileNotFoundError, MissingDependencyError, TranslationError) as exc:
        parser.exit(2, f"error: {exc}\n")

    print(f"Converted {args.pdf} into {args.output}")
    print(f"Segments translated: {len(segments)}")
    print(f"Review: {args.output / 'review.html'}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
