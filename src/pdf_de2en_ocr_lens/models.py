from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal


SegmentSource = Literal["native", "ocr"]


@dataclass(frozen=True)
class Segment:
    page: int
    source: SegmentSource
    text: str
    bbox: tuple[float, float, float, float] | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class TranslatedSegment:
    page: int
    source: SegmentSource
    original: str
    translated: str
    bbox: tuple[float, float, float, float] | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)
