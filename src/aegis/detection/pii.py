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

# Words that NER frequently misclassifies as PERSON or LOCATION in tech context
KNOWN_TECH_TERMS = {
    # Companies & products
    "anthropic", "openai", "google", "microsoft", "amazon", "meta", "apple",
    "github", "gitlab", "bitbucket", "docker", "kubernetes", "terraform",
    "slack", "discord", "stripe", "twilio", "sendgrid", "datadog", "splunk",
    "juspay", "razorpay", "paytm", "grafana", "vercel", "netlify", "heroku",
    "aws", "gcp", "azure",
    # Databases & infra
    "redis", "postgres", "mongodb", "elasticsearch", "nginx", "apache", "kafka",
    "mysql", "sqlite", "dynamodb", "cassandra",
    # Frameworks & languages
    "fastapi", "django", "flask", "react", "angular", "vue", "node", "rust",
    "python", "java", "typescript", "javascript", "golang", "ruby", "swift",
    "html", "css", "json", "yaml", "xml", "sql", "graphql",
    # AI models & tools
    "claude", "copilot", "codex", "gemini", "llama", "mistral", "gpt",
    "openrouter", "ollama", "huggingface",
    # OS & shells
    "ubuntu", "debian", "alpine", "centos", "linux", "darwin", "windows",
    "macos", "ios", "android",
    "bash", "zsh", "fish", "powershell",
    # Security terms NER misclassifies
    "xss", "csrf", "cors", "oauth", "jwt", "ssl", "tls", "ssh", "http", "https",
    "owasp", "cve", "sql",
    # Common English words NER misclassifies
    "skill", "tone", "write", "types", "mark", "system", "agent", "model",
    "prompt", "token", "tool", "hook", "plan", "task", "test", "build",
    "deploy", "config", "status", "error", "debug", "trace", "log",
    "read", "edit", "fetch", "push", "pull", "merge", "branch", "commit",
    "ai", "ml", "llm", "nlp", "api", "url", "uri", "ip",
}

# Tech words that appear in multi-word false positives
TECH_CONTEXT_WORDS = {
    "cloud", "platform", "studio", "engine", "server", "client",
    "framework", "runtime", "proxy", "gateway", "hub", "lab",
    "code", "data", "web", "app", "net", "base", "stack",
    "api", "sdk", "cli", "os", "shell", "version", "model",
    "injection", "attack", "vulnerability", "endpoint", "middleware",
    "container", "cluster", "pipeline", "workflow", "service",
}


def _is_ner_false_positive(text: str, start: int, end: int, value: str) -> bool:
    """Heuristic: is this NER detection (PERSON or LOCATION) likely a false positive?"""
    val_lower = value.lower()
    words = set(val_lower.split())

    # Any word is a known tech term
    if words & KNOWN_TECH_TERMS:
        return True

    # Contains tech context words
    if words & TECH_CONTEXT_WORDS:
        return True

    # Single word, all lowercase or all uppercase — unlikely to be a real name/location
    if " " not in value and (value.islower() or value.isupper()):
        return True

    # Contains punctuation/symbols — not a real name or place
    if any(c in value for c in "-/:@#&=+[]{}()<>"):
        return True

    # camelCase or PascalCase with no spaces — likely a code identifier
    if " " not in value and len(value) > 1 and any(c.isupper() for c in value[1:]) and any(c.islower() for c in value):
        # But allow normal names like "McDonald" — check if it has 2+ uppercase transitions
        upper_transitions = sum(1 for i in range(1, len(value)) if value[i].isupper() and value[i-1].islower())
        if upper_transitions >= 2:
            return True

    # Followed by possessive + org-like words: "Anthropic's official"
    after = text[end:end + 30].lower()
    if after.startswith("'s ") or after.startswith("\u2019s "):
        org_signals = ["official", "api", "sdk", "cli", "platform", "service",
                       "tool", "product", "team", "engineering", "cloud"]
        if any(signal in after for signal in org_signals):
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

            # Filter out tech terms misidentified as PERSON or LOCATION
            if result.entity_type in NER_ENTITIES and _is_ner_false_positive(text, result.start, result.end, value):
                continue

            detections.append(Detection(
                entity_type=result.entity_type,
                value=value,
                start=result.start,
                end=result.end,
            ))
        return detections
