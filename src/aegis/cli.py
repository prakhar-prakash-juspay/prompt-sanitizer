import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import click
import yaml
from rich.console import Console
from rich.table import Table

from aegis import __version__
from aegis.audit.reader import AuditReader
from aegis.config import load_config, default_config
from aegis.detection.allowlist import Allowlist

console = Console()


def get_aegis_home() -> Path:
    return Path(os.environ.get("AEGIS_HOME", "~/.aegis")).expanduser()


@click.group()
@click.version_option(version=__version__)
def cli():
    """Prompt Sanitizer - protect your LLM API calls from leaking secrets and PII."""
    pass


AEGIS_SHELL_MARKER = "# Prompt Sanitizer"

AEGIS_ENV_LINES = [
    AEGIS_SHELL_MARKER,
    "export ANTHROPIC_BASE_URL=http://localhost:8443/anthropic",
    "export OPENAI_BASE_URL=http://localhost:8443/openai",
]


def _detect_shell_profile() -> Path:
    shell = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        return Path("~/.zshrc").expanduser()
    return Path("~/.bashrc").expanduser()


def _shell_already_configured(profile: Path) -> bool:
    if not profile.exists():
        return False
    return AEGIS_SHELL_MARKER in profile.read_text()


def _configure_shell_profile(profile: Path) -> bool:
    """Append env vars to shell profile. Returns True if modified."""
    if _shell_already_configured(profile):
        return False
    with open(profile, "a") as f:
        f.write("\n" + "\n".join(AEGIS_ENV_LINES) + "\n")
    return True


def _detect_agents() -> list[dict]:
    """Detect installed agentic coding tools."""
    agents = []
    # Claude Code
    claude_dir = Path("~/.claude").expanduser()
    if claude_dir.exists() or shutil.which("claude"):
        agents.append({"name": "Claude Code", "env_var": "ANTHROPIC_BASE_URL"})
    # OpenAI Codex CLI
    if shutil.which("codex"):
        agents.append({"name": "OpenAI Codex", "env_var": "OPENAI_BASE_URL"})
    # GitHub Copilot (VS Code extension — check via code CLI)
    if shutil.which("code"):
        agents.append({"name": "VS Code (Copilot)", "env_var": "OPENAI_BASE_URL"})
    return agents


@cli.command()
@click.option("--skip-shell", is_flag=True, help="Skip auto-configuring shell profile")
def setup(skip_shell: bool):
    """One-time setup: create config, configure shell, detect agents. Fully automatic."""
    aegis_home = get_aegis_home()
    aegis_home.mkdir(parents=True, exist_ok=True)

    # 1. Create config
    config_path = aegis_home / "config.yaml"
    if not config_path.exists():
        config = default_config()
        config_dict = {
            "port": config.port,
            "viewer_port": config.viewer_port,
            "providers": {
                name: {"upstream": p.upstream}
                for name, p in config.providers.items()
            },
            "detection": {
                "secrets": config.detection.secrets,
                "pii": config.detection.pii,
                "infra": config.detection.infra,
                "custom_patterns": [],
            },
            "logging": {
                "audit_file": str(aegis_home / "audit.log"),
                "log_original_values": True,
                "store_request_body": True,
                "store_response_body": True,
            },
        }
        with open(config_path, "w") as f:
            yaml.dump(config_dict, f, default_flow_style=False)
    console.print(f"[green]✓[/green] Config at {config_path}")

    # 2. Create allowlist
    allowlist_path = aegis_home / "allowlist.yaml"
    if not allowlist_path.exists():
        allowlist_path.write_text("allowed: []\n")
    console.print(f"[green]✓[/green] Allowlist at {allowlist_path}")

    # 3. Auto-configure shell profile
    if not skip_shell:
        profile = _detect_shell_profile()
        if _configure_shell_profile(profile):
            console.print(f"[green]✓[/green] Added env vars to {profile}")
        else:
            console.print(f"[dim]✓[/dim] Shell profile already configured ({profile})")
    else:
        console.print("[dim]—[/dim] Skipped shell configuration")

    # 4. Detect agents
    agents = _detect_agents()
    if agents:
        console.print()
        console.print("[bold]Detected agents:[/bold]")
        for agent in agents:
            console.print(f"  [green]✓[/green] {agent['name']} — will route through proxy via {agent['env_var']}")
    else:
        console.print()
        console.print("[dim]No known agents detected. Prompt Sanitizer will protect any tool that uses:")
        console.print("  ANTHROPIC_BASE_URL or OPENAI_BASE_URL[/dim]")

    console.print()
    console.print("[bold]Setup complete.[/bold] Open a new terminal and run [bold]prompt-sanitizer start[/bold].")


@cli.command(name="configure-shell")
def configure_shell():
    """Auto-append base URL env vars to shell profile (idempotent)."""
    profile = _detect_shell_profile()
    if _configure_shell_profile(profile):
        console.print(f"[green]✓[/green] Added env vars to {profile}")
        console.print(f"Run [bold]source {profile}[/bold] or open a new terminal.")
    else:
        console.print(f"[dim]✓[/dim] Shell profile already configured ({profile})")


@cli.command()
def start():
    """Start the proxy."""
    aegis_home = get_aegis_home()
    config_path = aegis_home / "config.yaml"
    config = load_config(config_path)

    console.print(f"[green]✓[/green] Starting prompt-sanitizer on localhost:{config.port}")
    console.print(f"[green]✓[/green] Log viewer on localhost:{config.viewer_port}")

    import uvicorn
    from aegis.proxy.app import create_app

    allowlist_path = aegis_home / "allowlist.yaml"
    app = create_app(config, allowlist_path=allowlist_path, include_viewer=True)

    uvicorn.run(app, host="0.0.0.0", port=config.port)


@cli.command()
def stop():
    """Stop the proxy."""
    console.print("[yellow]Stop not yet implemented for non-service mode.[/yellow]")
    console.print("Use Ctrl+C or kill the process.")


@cli.command()
def status():
    """Show proxy status."""
    import httpx
    aegis_home = get_aegis_home()
    config = load_config(aegis_home / "config.yaml")
    try:
        resp = httpx.get(f"http://localhost:{config.port}/health", timeout=2)
        console.print(f"[green]✓[/green] Prompt Sanitizer is running on port {config.port}")
    except Exception:
        console.print(f"[red]✗[/red] Prompt Sanitizer is not running")


@cli.command()
@click.option("--summary", is_flag=True, help="Show redaction summary stats")
@click.option("--web", is_flag=True, help="Open log viewer in browser")
def log(summary: bool, web: bool):
    """View the audit log."""
    aegis_home = get_aegis_home()
    config = load_config(aegis_home / "config.yaml")
    # Resolve audit log path relative to aegis_home when using the default
    audit_file_path = config.audit_file_path
    default_audit = Path("~/.aegis/audit.log").expanduser()
    if audit_file_path == default_audit:
        audit_file_path = aegis_home / "audit.log"
    reader = AuditReader(audit_file_path)

    if web:
        import webbrowser
        webbrowser.open(f"http://localhost:{config.viewer_port}")
        return

    if summary:
        stats = reader.summary()
        console.print(f"Total requests: {stats['total_requests']}")
        console.print(f"Total redactions: {stats['total_redactions']}")
        if stats["redactions_by_type"]:
            table = Table(title="Redactions by Type")
            table.add_column("Type")
            table.add_column("Count", justify="right")
            for rtype, count in sorted(stats["redactions_by_type"].items()):
                table.add_row(rtype, str(count))
            console.print(table)
        return

    entries = reader.list_entries(limit=20)
    for entry in entries:
        ts = entry.get("timestamp", "?")
        provider = entry.get("provider", "?")
        redaction_count = len(entry.get("redactions", []))
        rid = entry.get("request_id", "?")
        if redaction_count > 0:
            console.print(f"[dim]{ts}[/dim] [{provider}] {rid} — [red]{redaction_count} redactions[/red]")
        else:
            console.print(f"[dim]{ts}[/dim] [{provider}] {rid} — [green]clean[/green]")


@cli.command()
@click.argument("value")
@click.option("--reason", default="", help="Reason for allowlisting")
def allow(value: str, reason: str):
    """Add a value to the allowlist."""
    aegis_home = get_aegis_home()
    allowlist_path = aegis_home / "allowlist.yaml"
    allowlist = Allowlist(allowlist_path)
    allowlist.add_value(value, reason=reason)
    console.print(f"[green]✓[/green] Added to allowlist: {value}")


@cli.command()
def config():
    """Open config file in editor."""
    aegis_home = get_aegis_home()
    config_path = aegis_home / "config.yaml"
    editor = os.environ.get("EDITOR", "vi")
    subprocess.run([editor, str(config_path)])


@cli.command()
def install():
    """Register as a system service (auto-start on boot)."""
    from aegis.service.installer import ServiceInstaller
    installer = ServiceInstaller()
    aegis_bin = shutil.which("prompt-sanitizer") or sys.executable + " -m aegis"
    result = installer.install(aegis_bin)
    console.print(f"[green]✓[/green] {result}")


@cli.command()
def uninstall():
    """Remove the system service."""
    from aegis.service.installer import ServiceInstaller
    installer = ServiceInstaller()
    result = installer.uninstall()
    console.print(f"[green]✓[/green] {result}")
