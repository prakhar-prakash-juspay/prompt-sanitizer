from pathlib import Path

from fastapi import FastAPI

from aegis.config import AegisConfig
from aegis.detection.allowlist import Allowlist
from aegis.proxy.router import ProxyRouter


def create_app(config: AegisConfig, allowlist_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Aegis Proxy", version="0.1.0")

    if allowlist_path is None:
        allowlist_path = Path("~/.aegis/allowlist.yaml").expanduser()

    allowlist = Allowlist(allowlist_path)
    proxy = ProxyRouter(config=config, allowlist=allowlist)
    app.include_router(proxy.router)

    return app
