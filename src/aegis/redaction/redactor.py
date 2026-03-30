import hashlib
from dataclasses import dataclass, field

from aegis.detection.engine import Detection


@dataclass
class RedactionResult:
    redacted_text: str
    redaction_map: dict[str, dict]  # placeholder -> {original, type, source}


def _make_placeholder(entity_type: str, value: str) -> str:
    hash_suffix = hashlib.sha256(value.encode()).hexdigest()[:6]
    return f"[REDACTED:{entity_type}:{hash_suffix}]"


class Redactor:
    def redact(self, text: str, detections: list[Detection]) -> RedactionResult:
        if not detections:
            return RedactionResult(redacted_text=text, redaction_map={})

        redaction_map: dict[str, dict] = {}
        value_to_placeholder: dict[tuple[str, str], str] = {}

        for det in detections:
            key = (det.entity_type, det.value)
            if key not in value_to_placeholder:
                placeholder = _make_placeholder(det.entity_type, det.value)
                value_to_placeholder[key] = placeholder
                redaction_map[placeholder] = {
                    "original": det.value,
                    "type": det.entity_type,
                    "source": det.source,
                }

        sorted_detections = sorted(detections, key=lambda d: d.start, reverse=True)

        result = text
        replaced_ranges: list[tuple[int, int]] = []

        for det in sorted_detections:
            if any(det.start < end and det.end > start for start, end in replaced_ranges):
                continue

            key = (det.entity_type, det.value)
            placeholder = value_to_placeholder[key]
            result = result[:det.start] + placeholder + result[det.end:]
            replaced_ranges.append((det.start, det.end))

        return RedactionResult(redacted_text=result, redaction_map=redaction_map)
