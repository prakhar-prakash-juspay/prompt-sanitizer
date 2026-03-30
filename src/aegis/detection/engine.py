from dataclasses import dataclass

from aegis.config import DetectionConfig, CustomPattern
from aegis.detection.allowlist import Allowlist
from aegis.detection.secrets import SecretDetector, Detection as SecretDetection
from aegis.detection.pii import PiiDetector, Detection as PiiDetection


@dataclass
class Detection:
    entity_type: str
    value: str
    start: int
    end: int
    source: str  # "secrets" or "pii"


class DetectionEngine:
    def __init__(self, config: DetectionConfig, allowlist: Allowlist):
        self._config = config
        self._allowlist = allowlist
        self._secret_detector = SecretDetector()
        self._pii_detector = PiiDetector()

        for cp in config.custom_patterns:
            self._secret_detector.add_custom_pattern(cp.name, cp.pattern)

    def detect(self, text: str) -> list[Detection]:
        detections: list[Detection] = []

        if self._config.secrets:
            for d in self._secret_detector.detect(text):
                if not self._allowlist.is_allowed(d.value):
                    detections.append(Detection(
                        entity_type=d.entity_type,
                        value=d.value,
                        start=d.start,
                        end=d.end,
                        source="secrets",
                    ))

        if self._config.pii:
            for d in self._pii_detector.detect(text):
                if not self._allowlist.is_allowed(d.value):
                    detections.append(Detection(
                        entity_type=d.entity_type,
                        value=d.value,
                        start=d.start,
                        end=d.end,
                        source="pii",
                    ))

        return self._deduplicate(detections)

    def _deduplicate(self, detections: list[Detection]) -> list[Detection]:
        seen: set[tuple[str, int, int]] = set()
        unique: list[Detection] = []
        for d in detections:
            key = (d.value, d.start, d.end)
            if key not in seen:
                seen.add(key)
                unique.append(d)
        return unique
