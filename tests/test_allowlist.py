import pytest
from pathlib import Path
from aegis.detection.allowlist import Allowlist


class TestAllowlist:
    def test_empty_allowlist_allows_nothing(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        path.write_text("allowed: []\n")
        al = Allowlist(path)
        assert al.is_allowed("AKIAIOSFODNN7EXAMPLE") is False

    def test_exact_value_match(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        path.write_text("""allowed:
  - value: "sha256:abc123"
    reason: "Docker digest"
""")
        al = Allowlist(path)
        assert al.is_allowed("sha256:abc123") is True
        assert al.is_allowed("sha256:other") is False

    def test_pattern_match(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        path.write_text("""allowed:
  - pattern: "TEST_.*"
    reason: "Test fixtures"
""")
        al = Allowlist(path)
        assert al.is_allowed("TEST_API_KEY_12345") is True
        assert al.is_allowed("PROD_API_KEY") is False

    def test_add_value_persists(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        path.write_text("allowed: []\n")
        al = Allowlist(path)
        al.add_value("sha256:abc123", reason="Docker digest")

        # Reload and verify
        al2 = Allowlist(path)
        assert al2.is_allowed("sha256:abc123") is True

    def test_missing_file_creates_empty(self, tmp_aegis_dir):
        path = tmp_aegis_dir / "allowlist.yaml"
        al = Allowlist(path)
        assert al.is_allowed("anything") is False
