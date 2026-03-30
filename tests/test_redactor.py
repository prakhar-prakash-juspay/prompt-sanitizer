import pytest
from aegis.redaction.redactor import Redactor, RedactionResult
from aegis.detection.engine import Detection


class TestRedactor:
    @pytest.fixture
    def redactor(self):
        return Redactor()

    def test_redacts_single_detection(self, redactor):
        text = "My key is AKIAIOSFODNN7EXAMPLE"
        detections = [Detection(
            entity_type="AWS_KEY",
            value="AKIAIOSFODNN7EXAMPLE",
            start=10,
            end=30,
            source="secrets",
        )]
        result = redactor.redact(text, detections)
        assert "AKIAIOSFODNN7EXAMPLE" not in result.redacted_text
        assert "[REDACTED:AWS_KEY:" in result.redacted_text
        assert len(result.redaction_map) == 1

    def test_redacts_multiple_detections(self, redactor):
        text = "Key AKIAIOSFODNN7EXAMPLE and email john@example.com"
        detections = [
            Detection(entity_type="AWS_KEY", value="AKIAIOSFODNN7EXAMPLE", start=4, end=24, source="secrets"),
            Detection(entity_type="EMAIL_ADDRESS", value="john@example.com", start=35, end=51, source="pii"),
        ]
        result = redactor.redact(text, detections)
        assert "AKIAIOSFODNN7EXAMPLE" not in result.redacted_text
        assert "john@example.com" not in result.redacted_text
        assert len(result.redaction_map) == 2

    def test_placeholder_has_unique_hash(self, redactor):
        text = "Key AKIAIOSFODNN7EXAMPLE here"
        detections = [Detection(
            entity_type="AWS_KEY",
            value="AKIAIOSFODNN7EXAMPLE",
            start=4,
            end=24,
            source="secrets",
        )]
        result = redactor.redact(text, detections)
        placeholder = list(result.redaction_map.keys())[0]
        parts = placeholder.strip("[]").split(":")
        assert parts[0] == "REDACTED"
        assert parts[1] == "AWS_KEY"
        assert len(parts[2]) == 6  # 6-char hash

    def test_redaction_map_has_original_values(self, redactor):
        text = "Email john@example.com"
        detections = [Detection(
            entity_type="EMAIL_ADDRESS",
            value="john@example.com",
            start=6,
            end=22,
            source="pii",
        )]
        result = redactor.redact(text, detections)
        placeholder = list(result.redaction_map.keys())[0]
        entry = result.redaction_map[placeholder]
        assert entry["original"] == "john@example.com"
        assert entry["type"] == "EMAIL_ADDRESS"

    def test_no_detections_returns_original(self, redactor):
        text = "Nothing sensitive here"
        result = redactor.redact(text, [])
        assert result.redacted_text == text
        assert len(result.redaction_map) == 0

    def test_same_value_different_positions_get_same_placeholder(self, redactor):
        text = "john@example.com and john@example.com again"
        detections = [
            Detection(entity_type="EMAIL_ADDRESS", value="john@example.com", start=0, end=16, source="pii"),
            Detection(entity_type="EMAIL_ADDRESS", value="john@example.com", start=21, end=37, source="pii"),
        ]
        result = redactor.redact(text, detections)
        assert result.redacted_text.count("[REDACTED:EMAIL_ADDRESS:") == 2
        assert len(result.redaction_map) == 1  # only one unique mapping
