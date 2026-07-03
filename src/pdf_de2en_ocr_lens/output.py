from __future__ import annotations

import html
import json
from pathlib import Path

from .models import TranslatedSegment


def write_outputs(segments: list[TranslatedSegment], output_dir: Path, source_pdf: Path, translator_name: str) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "translation.md").write_text(render_markdown(segments, source_pdf, translator_name), encoding="utf-8")
    (output_dir / "segments.json").write_text(
        json.dumps([segment.to_dict() for segment in segments], indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "review.html").write_text(render_review_html(segments, source_pdf, translator_name), encoding="utf-8")


def render_markdown(segments: list[TranslatedSegment], source_pdf: Path, translator_name: str) -> str:
    lines = [
        f"# English Translation: {source_pdf.name}",
        "",
        f"Translator: `{translator_name}`",
        "",
    ]
    current_page = None
    for segment in segments:
        if segment.page != current_page:
            current_page = segment.page
            lines.extend([f"## Page {current_page}", ""])
        tag = "OCR" if segment.source == "ocr" else "PDF text"
        lines.extend(
            [
                f"**{tag}:** {segment.translated}",
                "",
                f"<details><summary>Original German</summary>",
                "",
                segment.original,
                "",
                "</details>",
                "",
            ]
        )
    return "\n".join(lines)


def render_review_html(segments: list[TranslatedSegment], source_pdf: Path, translator_name: str) -> str:
    rows = []
    for segment in segments:
        bbox = "" if segment.bbox is None else ", ".join(f"{value:.1f}" for value in segment.bbox)
        confidence = "" if segment.confidence is None else f"{segment.confidence:.1f}"
        rows.append(
            "<tr>"
            f"<td>{segment.page}</td>"
            f"<td>{html.escape(segment.source)}</td>"
            f"<td>{confidence}</td>"
            f"<td>{html.escape(segment.original)}</td>"
            f"<td>{html.escape(segment.translated)}</td>"
            f"<td>{html.escape(bbox)}</td>"
            "</tr>"
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>PDF Translation Review</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 32px; color: #17202a; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #ccd3dc; padding: 8px; vertical-align: top; }}
    th {{ background: #eef3f8; text-align: left; }}
    .meta {{ color: #52616f; }}
  </style>
</head>
<body>
  <h1>PDF Translation Review</h1>
  <p class="meta">Source: {html.escape(source_pdf.name)} | Translator: {html.escape(translator_name)}</p>
  <table>
    <thead>
      <tr><th>Page</th><th>Source</th><th>OCR confidence</th><th>German</th><th>English</th><th>Box</th></tr>
    </thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
</body>
</html>
"""
