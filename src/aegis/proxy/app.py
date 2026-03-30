from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from aegis.config import AegisConfig
from aegis.detection.allowlist import Allowlist
from aegis.proxy.router import ProxyRouter


def create_app(
    config: AegisConfig,
    allowlist_path: Path | None = None,
    include_viewer: bool = False,
) -> FastAPI:
    app = FastAPI(title="Prompt Sanitizer", version="0.1.0")

    if allowlist_path is None:
        allowlist_path = Path("~/.aegis/allowlist.yaml").expanduser()

    allowlist = Allowlist(allowlist_path)

    @app.get("/health")
    def health():
        return {"status": "ok", "version": "0.1.0"}

    # Viewer API + static files MUST be registered before the proxy catch-all
    if include_viewer:
        from aegis.audit.reader import AuditReader
        from aegis.viewer.api import create_viewer_router

        reader = AuditReader(config.audit_file_path)
        viewer_router = create_viewer_router(reader, allowlist)
        app.include_router(viewer_router)

        static_dir = Path(__file__).parent.parent / "viewer" / "static"
        if static_dir.exists():
            app.mount("/viewer", StaticFiles(directory=str(static_dir), html=True), name="viewer")

    # Proxy catch-all MUST be last
    proxy = ProxyRouter(config=config, allowlist=allowlist)
    app.include_router(proxy.router)

    return app
