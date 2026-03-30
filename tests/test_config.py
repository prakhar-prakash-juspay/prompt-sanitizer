import pytest
from pathlib import Path
from aegis.config import AegisConfig, load_config, default_config


class TestDefaultConfig:
    def test_default_config_has_required_fields(self):
        config = default_config()
        assert config.port == 8443
        assert config.viewer_port == 8444
        assert "anthropic" in config.providers
        assert "openai" in config.providers
        assert config.detection.secrets is True
        assert config.detection.pii is True

    def test_default_providers_have_upstream_urls(self):
        config = default_config()
        assert config.providers["anthropic"].upstream == "https://api.anthropic.com"
        assert config.providers["openai"].upstream == "https://api.openai.com"


class TestLoadConfig:
    def test_load_config_from_file(self, tmp_config_file):
        config = load_config(tmp_config_file)
        assert config.port == 8443
        assert config.providers["anthropic"].upstream == "https://api.anthropic.com"

    def test_load_config_missing_file_returns_default(self, tmp_path):
        config = load_config(tmp_path / "nonexistent.yaml")
        assert config.port == 8443

    def test_load_config_custom_port(self, tmp_aegis_dir):
        config_path = tmp_aegis_dir / "config.yaml"
        config_path.write_text("port: 9999\nviewer_port: 9998\nproviders:\n  anthropic:\n    upstream: https://api.anthropic.com\ndetection:\n  secrets: true\n  pii: true\n  infra: true\n  custom_patterns: []\nlogging:\n  audit_file: /tmp/audit.log\n  log_original_values: true\n  store_request_body: true\n  store_response_body: true\n")
        config = load_config(config_path)
        assert config.port == 9999

    def test_load_config_custom_patterns(self, tmp_aegis_dir):
        config_path = tmp_aegis_dir / "config.yaml"
        config_path.write_text("""port: 8443
viewer_port: 8444
providers:
  anthropic:
    upstream: https://api.anthropic.com
detection:
  secrets: true
  pii: true
  infra: true
  custom_patterns:
    - name: project_id
      pattern: "PROJ-[A-Z0-9]{8}"
logging:
  audit_file: /tmp/audit.log
  log_original_values: true
  store_request_body: true
  store_response_body: true
""")
        config = load_config(config_path)
        assert len(config.detection.custom_patterns) == 1
        assert config.detection.custom_patterns[0].name == "project_id"
