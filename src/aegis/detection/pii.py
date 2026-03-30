from dataclasses import dataclass

from presidio_analyzer import AnalyzerEngine


@dataclass
class Detection:
    entity_type: str
    value: str
    start: int
    end: int


# Entity types Presidio should look for
ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "IP_ADDRESS",
    "IBAN_CODE",
    "PERSON",
    "LOCATION",
]


class PiiDetector:
    def __init__(self):
        self._analyzer = AnalyzerEngine()

    def detect(self, text: str) -> list[Detection]:
        results = self._analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language="en",
        )

        detections = []
        for result in results:
            detections.append(Detection(
                entity_type=result.entity_type,
                value=text[result.start:result.end],
                start=result.start,
                end=result.end,
            ))
        return detections
