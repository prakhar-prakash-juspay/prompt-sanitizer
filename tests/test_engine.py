import pytest
from aegis.detection.engine import DetectionEngine
from aegis.detection.allowlist import Allowlist
from aegis.config import DetectionConfig


class TestDetectionEngine:
    @pytest.fixture
    def engine(self, tmp_empty_allowlist):
        config = DetectionConfig(secrets=True, pii=True, infra=True, custom_patterns=[])
        allowlist = Allowlist(tmp_empty_allowlist)
        return DetectionEngine(config=config, allowlist=allowlist)

    def test_detects_both_secrets_and_pii(self, engine):
        text = "Key AKIAIOSFODNN7EXAMPLE and email john@example.com"
        detections = engine.detect(text)
        types = {d.entity_type for d in detections}
        assert "AWS_KEY" in types
        assert "EMAIL_ADDRESS" in types

    def test_respects_allowlist(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        path.write_text("""allowed:
  - value: "AKIAIOSFODNN7EXAMPLE"
    reason: "test key"
""")
        config = DetectionConfig(secrets=True, pii=True, infra=True, custom_patterns=[])
        allowlist = Allowlist(path)
        engine = DetectionEngine(config=config, allowlist=allowlist)
        text = "Key AKIAIOSFODNN7EXAMPLE here"
        detections = engine.detect(text)
        assert not any(d.value == "AKIAIOSFODNN7EXAMPLE" for d in detections)

    def test_secrets_disabled(self, tmp_empty_allowlist):
        config = DetectionConfig(secrets=False, pii=True, infra=True, custom_patterns=[])
        allowlist = Allowlist(tmp_empty_allowlist)
        engine = DetectionEngine(config=config, allowlist=allowlist)
        text = "Key AKIAIOSFODNN7EXAMPLE here"
        detections = engine.detect(text)
        assert not any(d.entity_type == "AWS_KEY" for d in detections)

    def test_pii_disabled(self, tmp_empty_allowlist):
        config = DetectionConfig(secrets=True, pii=False, infra=True, custom_patterns=[])
        allowlist = Allowlist(tmp_empty_allowlist)
        engine = DetectionEngine(config=config, allowlist=allowlist)
        text = "Email john@example.com"
        detections = engine.detect(text)
        assert not any(d.entity_type == "EMAIL_ADDRESS" for d in detections)

    def test_deduplicates_overlapping_detections(self, engine):
        text = "Contact admin@secret-internal-server.corp.example.com"
        detections = engine.detect(text)
        seen = set()
        for d in detections:
            key = (d.value, d.start, d.end)
            assert key not in seen, f"Duplicate detection: {key}"
            seen.add(key)
