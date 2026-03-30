import platform
import shutil
import subprocess
from pathlib import Path


SYSTEMD_UNIT_TEMPLATE = """[Unit]
Description=Prompt Sanitizer — LLM API secret and PII redaction proxy
After=network.target

[Service]
Type=simple
ExecStart={aegis_bin} start
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
"""

LAUNCHD_PLIST_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.prompt-sanitizer</string>
    <key>ProgramArguments</key>
    <array>
        <string>{aegis_bin}</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
"""


class ServiceInstaller:
    def detect_init_system(self) -> str:
        system = platform.system()
        if system == "Darwin":
            return "launchd"
        if system == "Linux" and shutil.which("systemctl"):
            return "systemd"
        return "unknown"

    def generate_systemd_unit(self, aegis_bin: str) -> str:
        return SYSTEMD_UNIT_TEMPLATE.format(aegis_bin=aegis_bin)

    def generate_launchd_plist(self, aegis_bin: str) -> str:
        return LAUNCHD_PLIST_TEMPLATE.format(aegis_bin=aegis_bin)

    def install(self, aegis_bin: str) -> str:
        init_system = self.detect_init_system()

        if init_system == "systemd":
            unit_path = Path("/etc/systemd/system/prompt-sanitizer.service")
            unit_path.write_text(self.generate_systemd_unit(aegis_bin))
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            subprocess.run(["systemctl", "enable", "prompt-sanitizer"], check=True)
            subprocess.run(["systemctl", "start", "prompt-sanitizer"], check=True)
            return f"Installed systemd service at {unit_path}"

        elif init_system == "launchd":
            plist_path = Path.home() / "Library/LaunchAgents/com.prompt-sanitizer.plist"
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(self.generate_launchd_plist(aegis_bin))
            subprocess.run(["launchctl", "load", str(plist_path)], check=True)
            return f"Installed launchd service at {plist_path}"

        else:
            return "Unknown init system. Please start manually with: prompt-sanitizer start"

    def uninstall(self) -> str:
        init_system = self.detect_init_system()

        if init_system == "systemd":
            subprocess.run(["systemctl", "stop", "prompt-sanitizer"], check=False)
            subprocess.run(["systemctl", "disable", "prompt-sanitizer"], check=False)
            unit_path = Path("/etc/systemd/system/prompt-sanitizer.service")
            if unit_path.exists():
                unit_path.unlink()
            subprocess.run(["systemctl", "daemon-reload"], check=True)
            return "Removed systemd service"

        elif init_system == "launchd":
            plist_path = Path.home() / "Library/LaunchAgents/com.prompt-sanitizer.plist"
            if plist_path.exists():
                subprocess.run(["launchctl", "unload", str(plist_path)], check=False)
                plist_path.unlink()
            return "Removed launchd service"

        else:
            return "Unknown init system. Nothing to uninstall."
