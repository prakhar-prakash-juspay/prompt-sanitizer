from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aegis.config import AegisConfig
from aegis.detection.allowlist import Allowlist
from aegis.proxy.router import ProxyRouter


def create_app(config: AegisConfig, allowlist_path: Path | None = None) -> FastAPI:
    app = FastAPI(title="Prompt Sanitizer", version="0.1.0")

    if allowlist_path is None:
        allowlist_path = Path("~/.aegis/allowlist.yaml").expanduser()

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    allowlist = Allowlist(allowlist_path)
    proxy = ProxyRouter(config=config, allowlist=allowlist)
    app.include_router(proxy.router)

    # Serve viewer static files if they exist
    static_dir = Path(__file__).parent.parent / "viewer" / "static"
    if static_dir.exists():
        app.mount("/viewer", StaticFiles(directory=str(static_dir), html=True), name="viewer")

    return app
