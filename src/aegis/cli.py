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
    """Aegis Proxy - protect your LLM API calls from leaking secrets and PII."""
    pass


@cli.command()
def setup():
    """One-time setup: create config directory, default config, and allowlist."""
    aegis_home = get_aegis_home()
    aegis_home.mkdir(parents=True, exist_ok=True)

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

    allowlist_path = aegis_home / "allowlist.yaml"
    if not allowlist_path.exists():
        allowlist_path.write_text("allowed: []\n")

    console.print(f"[green]✓[/green] aegis config at {config_path}")
    console.print(f"[green]✓[/green] allowlist at {allowlist_path}")
    console.print()
    console.print("To route agents through aegis, set these environment variables:")
    console.print()
    console.print("  export ANTHROPIC_BASE_URL=http://localhost:8443/anthropic")
    console.print("  export OPENAI_BASE_URL=http://localhost:8443/openai")
    console.print()
    console.print("Or run: [bold]aegis configure-shell[/bold]")


@cli.command(name="configure-shell")
def configure_shell():
    """Auto-append base URL env vars to shell profile."""
    shell = os.environ.get("SHELL", "/bin/bash")
    if "zsh" in shell:
        profile = Path("~/.zshrc").expanduser()
    else:
        profile = Path("~/.bashrc").expanduser()

    lines = [
        "\n# Aegis Proxy",
        "export ANTHROPIC_BASE_URL=http://localhost:8443/anthropic",
        "export OPENAI_BASE_URL=http://localhost:8443/openai",
    ]

    with open(profile, "a") as f:
        f.write("\n".join(lines) + "\n")

    console.print(f"[green]✓[/green] Added aegis env vars to {profile}")
    console.print(f"Run [bold]source {profile}[/bold] or open a new terminal.")


@cli.command()
def start():
    """Start the aegis proxy."""
    aegis_home = get_aegis_home()
    config_path = aegis_home / "config.yaml"
    config = load_config(config_path)

    console.print(f"[green]✓[/green] Starting aegis proxy on localhost:{config.port}")
    console.print(f"[green]✓[/green] Log viewer on localhost:{config.viewer_port}")

    import uvicorn
    from aegis.proxy.app import create_app
    from aegis.viewer.api import create_viewer_router

    allowlist_path = aegis_home / "allowlist.yaml"
    app = create_app(config, allowlist_path=allowlist_path)

    reader = AuditReader(config.audit_file_path)
    allowlist = Allowlist(allowlist_path)
    viewer_router = create_viewer_router(reader, allowlist)
    app.include_router(viewer_router)

    uvicorn.run(app, host="0.0.0.0", port=config.port)


@cli.command()
def stop():
    """Stop the aegis proxy."""
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
        console.print(f"[green]✓[/green] Aegis proxy is running on port {config.port}")
    except Exception:
        console.print(f"[red]✗[/red] Aegis proxy is not running")


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
    """Register aegis as a system service (auto-start on boot)."""
    from aegis.service.installer import ServiceInstaller
    installer = ServiceInstaller()
    aegis_bin = shutil.which("aegis") or sys.executable + " -m aegis"
    result = installer.install(aegis_bin)
    console.print(f"[green]✓[/green] {result}")


@cli.command()
def uninstall():
    """Remove the aegis system service."""
    from aegis.service.installer import ServiceInstaller
    installer = ServiceInstaller()
    result = installer.uninstall()
    console.print(f"[green]✓[/green] {result}")
