from pdf_de2en_ocr_lens.models import Segment
from pdf_de2en_ocr_lens.pipeline import dedupe_segments


def test_dedupe_prefers_first_segment_order():
    segments = [
        Segment(page=1, source="native", text="RAN Metriken"),
        Segment(page=1, source="ocr", text="RAN Metriken"),
        Segment(page=1, source="ocr", text="Diagramm Label"),
    ]

    deduped = dedupe_segments(segments)

    assert [segment.text for segment in deduped] == ["RAN Metriken", "Diagramm Label"]
    assert deduped[0].source == "native"
