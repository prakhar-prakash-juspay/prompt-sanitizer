import json
import pytest
from click.testing import CliRunner
from aegis.cli import cli


@pytest.fixture
def runner():
    return CliRunner()


class TestCLI:
    def test_version(self, runner):
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.1.0" in result.output

    def test_setup_creates_config_dir(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        # Create a shell profile for setup to write to
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# existing config\n")
        monkeypatch.setenv("SHELL", "/bin/bash")
        monkeypatch.setattr("aegis.cli._detect_shell_profile", lambda: bashrc)
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        assert aegis_dir.exists()
        assert (aegis_dir / "config.yaml").exists()
        assert (aegis_dir / "allowlist.yaml").exists()

    def test_setup_auto_configures_shell(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# existing config\n")
        monkeypatch.setattr("aegis.cli._detect_shell_profile", lambda: bashrc)
        result = runner.invoke(cli, ["setup"])
        assert result.exit_code == 0
        content = bashrc.read_text()
        assert "ANTHROPIC_BASE_URL=http://localhost:8443/anthropic" in content
        assert "OPENAI_BASE_URL=http://localhost:8443/openai" in content

    def test_setup_idempotent_shell_config(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# existing config\n")
        monkeypatch.setattr("aegis.cli._detect_shell_profile", lambda: bashrc)
        # Run setup twice
        runner.invoke(cli, ["setup"])
        runner.invoke(cli, ["setup"])
        content = bashrc.read_text()
        # Should only appear once
        assert content.count("ANTHROPIC_BASE_URL") == 1

    def test_setup_skip_shell(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        bashrc = tmp_path / ".bashrc"
        bashrc.write_text("# existing config\n")
        monkeypatch.setattr("aegis.cli._detect_shell_profile", lambda: bashrc)
        result = runner.invoke(cli, ["setup", "--skip-shell"])
        assert result.exit_code == 0
        content = bashrc.read_text()
        assert "ANTHROPIC_BASE_URL" not in content

    def test_status_when_not_running(self, runner, tmp_path, monkeypatch):
        monkeypatch.setenv("AEGIS_HOME", str(tmp_path / ".aegis"))
        result = runner.invoke(cli, ["status"])
        assert result.exit_code == 0
        assert "not running" in result.output.lower()

    def test_log_summary(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        aegis_dir.mkdir()
        log_file = aegis_dir / "audit.log"
        entry = {"timestamp": "2026-03-30T10:00:00Z", "request_id": "req_001", "provider": "anthropic", "endpoint": "/v1/messages", "request_body": {}, "response_body": {}, "redactions": [{"type": "AWS_KEY", "placeholder": "[REDACTED:AWS_KEY:a1b2c3]", "original": "AKIA..."}]}
        log_file.write_text(json.dumps(entry) + "\n")
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        result = runner.invoke(cli, ["log", "--summary"])
        assert result.exit_code == 0
        assert "1" in result.output

    def test_allow_adds_to_allowlist(self, runner, tmp_path, monkeypatch):
        aegis_dir = tmp_path / ".aegis"
        aegis_dir.mkdir()
        (aegis_dir / "allowlist.yaml").write_text("allowed: []\n")
        monkeypatch.setenv("AEGIS_HOME", str(aegis_dir))
        result = runner.invoke(cli, ["allow", "sha256:abc123", "--reason", "Docker digest"])
        assert result.exit_code == 0
        assert "added" in result.output.lower()
