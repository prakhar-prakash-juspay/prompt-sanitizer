import os
import pytest
from pathlib import Path


@pytest.fixture
def tmp_aegis_dir(tmp_path):
    """Create a temporary ~/.aegis directory for testing."""
    aegis_dir = tmp_path / ".aegis"
    aegis_dir.mkdir()
    return aegis_dir


@pytest.fixture
def tmp_config_file(tmp_aegis_dir):
    """Create a minimal config file for testing."""
    config_path = tmp_aegis_dir / "config.yaml"
    config_path.write_text(
        """port: 8443
viewer_port: 8444

providers:
  anthropic:
    upstream: https://api.anthropic.com
  openai:
    upstream: https://api.openai.com

detection:
  secrets: true
  pii: true
  infra: true
  custom_patterns: []

logging:
  audit_file: {audit_file}
  log_original_values: true
  store_request_body: true
  store_response_body: true
""".format(audit_file=str(tmp_aegis_dir / "audit.log"))
    )
    return config_path


@pytest.fixture
def tmp_allowlist_file(tmp_aegis_dir):
    """Create an empty allowlist file for testing."""
    allowlist_path = tmp_aegis_dir / "allowlist.yaml"
    allowlist_path.write_text("allowed: []\n")
    return allowlist_path


@pytest.fixture
def tmp_audit_log(tmp_aegis_dir):
    """Return path to a temporary audit log file."""
    return tmp_aegis_dir / "audit.log"


@pytest.fixture
def tmp_empty_allowlist(tmp_aegis_dir):
    path = tmp_aegis_dir / "allowlist.yaml"
    path.write_text("allowed: []\n")
    return path
