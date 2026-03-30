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


# NER-based entities need higher confidence to avoid false positives
NER_ENTITIES = {"PERSON", "LOCATION"}
DEFAULT_NER_THRESHOLD = 0.7
DEFAULT_THRESHOLD = 0.3

# Single-word names that are almost always company/product names in code context
KNOWN_NON_PERSONS = {
    "anthropic", "openai", "google", "microsoft", "amazon", "meta", "apple",
    "github", "gitlab", "bitbucket", "docker", "kubernetes", "terraform",
    "slack", "discord", "stripe", "twilio", "sendgrid", "datadog", "splunk",
    "redis", "postgres", "mongodb", "elasticsearch", "nginx", "apache",
    "fastapi", "django", "flask", "react", "angular", "vue", "node",
    "claude", "copilot", "codex", "gemini", "llama", "mistral",
    "ubuntu", "debian", "alpine", "centos", "linux", "darwin", "windows",
    "juspay", "razorpay", "paytm",
}


def _looks_like_org(text: str, start: int, end: int, value: str) -> bool:
    """Heuristic: is this 'person' name likely an organization?"""
    val_lower = value.lower()

    # Single-word known non-persons
    if val_lower in KNOWN_NON_PERSONS:
        return True

    # Followed by possessive + org-like words: "Anthropic's official", "Google's API"
    after = text[end:end + 30].lower()
    if after.startswith("'s ") or after.startswith("'s "):
        org_signals = ["official", "api", "sdk", "cli", "platform", "service",
                       "tool", "product", "team", "engineering", "cloud"]
        if any(signal in after for signal in org_signals):
            return True

    # All-caps or camelCase — likely a product/brand, not a person
    if value.isupper() or (len(value) > 1 and value[0].isupper() and " " not in value and any(c.isupper() for c in value[1:])):
        return True

    # Contains tech/product words — not a person
    tech_words = {"cloud", "platform", "studio", "engine", "server", "client",
                  "framework", "runtime", "proxy", "gateway", "hub", "lab",
                  "code", "data", "web", "app", "net", "base", "stack"}
    if any(w in val_lower.split() for w in tech_words):
        return True

    return False


class PiiDetector:
    def __init__(
        self,
        model_name: str = "en_core_web_sm",
        ner_threshold: float = DEFAULT_NER_THRESHOLD,
    ):
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": model_name}],
        }
        nlp_engine = NlpEngineProvider(nlp_configuration=nlp_config).create_engine()
        self._analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        self._ner_threshold = ner_threshold

    def detect(self, text: str) -> list[Detection]:
        results = self._analyzer.analyze(
            text=text,
            entities=ENTITIES,
            language="en",
            score_threshold=DEFAULT_THRESHOLD,
        )

        detections = []
        for result in results:
            # Apply stricter threshold for NER-based entities
            if result.entity_type in NER_ENTITIES and result.score < self._ner_threshold:
                continue

            value = text[result.start:result.end]

            # Filter out org/product names misidentified as persons
            if result.entity_type == "PERSON" and _looks_like_org(text, result.start, result.end, value):
                continue

            detections.append(Detection(
                entity_type=result.entity_type,
                value=value,
                start=result.start,
                end=result.end,
            ))
        return detections
