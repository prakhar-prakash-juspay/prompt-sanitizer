from dataclasses import dataclass

from presidio_analyzer import AnalyzerEngine
from presidio_analyzer.nlp_engine import NlpEngineProvider


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
    def __init__(self, model_name: str = "en_core_web_sm"):
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": model_name}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
        self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine)

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
