import re
from dataclasses import dataclass


@dataclass
class Detection:
    entity_type: str
    value: str
    start: int
    end: int


# Patterns adapted from detect-secrets and common secret formats
BUILT_IN_PATTERNS: list[tuple[str, re.Pattern]] = [
    ("AWS_KEY", re.compile(r"(?<![A-Z0-9])(AKIA[0-9A-Z]{16})(?![A-Z0-9])")),
    ("PRIVATE_KEY", re.compile(r"-----BEGIN[A-Z\s]+PRIVATE KEY-----[\s\S]*?-----END[A-Z\s]+PRIVATE KEY-----")),
    ("JWT", re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}")),
    ("GITHUB_TOKEN", re.compile(r"(?<![A-Za-z0-9_])(gh[ps]_[A-Za-z0-9_]{36,})(?![A-Za-z0-9_])")),
    # Generic secret: key=value or key:value patterns (lowered to 8+ chars)
    ("GENERIC_SECRET", re.compile(
        r"""(?i)(?:api[_-]?key|api[_-]?secret|secret[_-]?key|access[_-]?token|auth[_-]?token|credentials|password|passwd|token|secret)"""
        r"""[\s]*[=:]\s*['"]?([A-Za-z0-9/+=_\-!@#$%^&*]{8,})['"]?"""
    )),
    ("CONNECTION_STRING", re.compile(
        r"(?:postgresql|mysql|mongodb|redis|amqp|sqlite)://[^\s\"'`,;]+"
    )),
    # Prefixed API keys (sk_, pk_, api_, etc.) and generic token-like strings (word-word-hex)
    ("PREFIXED_API_KEY", re.compile(
        r"(?<![A-Za-z0-9_-])((?:sk|pk|api|key|token|secret|test|demo|live|prod)[_-][A-Za-z0-9_-]{8,})(?![A-Za-z0-9_-])"
    )),
    # Generic token: word-word-hexstring (e.g., ind-test-9f8e7d6c5b4a)
    ("GENERIC_TOKEN", re.compile(
        r"(?<![A-Za-z0-9_-])([a-zA-Z]{2,10}-[a-zA-Z]{2,10}-[a-f0-9]{12,})(?![A-Za-z0-9_-])"
    )),
    ("STRIPE_KEY", re.compile(r"(?<![A-Za-z0-9_])(sk_live_[A-Za-z0-9]{20,})(?![A-Za-z0-9_])")),
    ("SENDGRID_KEY", re.compile(r"(?<![A-Za-z0-9_])(SG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43})(?![A-Za-z0-9_])")),
    ("TWILIO_KEY", re.compile(r"(?<![A-Za-z0-9_])(SK[a-f0-9]{32})(?![A-Za-z0-9_])")),
    ("SLACK_TOKEN", re.compile(r"(?<![A-Za-z0-9_])(xox[bpors]-[A-Za-z0-9-]{10,})(?![A-Za-z0-9_])")),
    # Password in prose: "password X", "password is X", "password to X", "set a password X"
    ("PASSWORD_IN_PROSE", re.compile(
        r"""(?i)(?:password|passwd|passcode)\s+(?:(?:is|was|to|of|set\s+to)\s+)?['"]?([^\s'",.]{6,})['"]?"""
    )),
    ("HIGH_ENTROPY_BASE64", re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{40,}={0,2}(?![A-Za-z0-9+/=])")),
    # International phone numbers
    ("PHONE_INTL", re.compile(r"(?<![A-Za-z0-9])(\+\d{1,3}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,6})(?![A-Za-z0-9])")),
]


class SecretDetector:
    def __init__(self):
        self._patterns: list[tuple[str, re.Pattern]] = list(BUILT_IN_PATTERNS)

    def add_custom_pattern(self, name: str, pattern: str) -> None:
        self._patterns.append((name, re.compile(pattern)))

    def detect(self, text: str) -> list[Detection]:
        detections: list[Detection] = []
        for entity_type, pattern in self._patterns:
            for match in pattern.finditer(text):
                # If the pattern has a capturing group, use it; otherwise use full match
                if match.lastindex and match.lastindex >= 1:
                    value = match.group(1)
                    start = match.start(1)
                    end = match.end(1)
                else:
                    value = match.group(0)
                    start = match.start(0)
                    end = match.end(0)
                detections.append(Detection(
                    entity_type=entity_type,
                    value=value,
                    start=start,
                    end=end,
                ))
        return detections
