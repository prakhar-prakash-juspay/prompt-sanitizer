import pytest
from pathlib import Path
from aegis.service.installer import ServiceInstaller


class TestServiceInstaller:
    def test_generate_systemd_unit(self):
        installer = ServiceInstaller()
        unit = installer.generate_systemd_unit("/usr/bin/aegis")
        assert "[Unit]" in unit
        assert "aegis" in unit.lower()
        assert "/usr/bin/aegis start" in unit

    def test_generate_launchd_plist(self):
        installer = ServiceInstaller()
        plist = installer.generate_launchd_plist("/usr/local/bin/aegis")
        assert "com.aegis.proxy" in plist
        assert "/usr/local/bin/aegis" in plist

    def test_detect_init_system_returns_string(self):
        installer = ServiceInstaller()
        result = installer.detect_init_system()
        assert result in ("systemd", "launchd", "unknown")
