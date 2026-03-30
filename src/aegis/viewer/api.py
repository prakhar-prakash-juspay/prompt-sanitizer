from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aegis.audit.reader import AuditReader
from aegis.detection.allowlist import Allowlist


class AllowlistRequest(BaseModel):
    value: str
    reason: str = ""


def create_viewer_router(reader: AuditReader, allowlist: Allowlist) -> APIRouter:
    router = APIRouter(prefix="/api")

    @router.get("/entries")
    def list_entries(provider: str | None = None, limit: int | None = None):
        return reader.list_entries(provider=provider, limit=limit)

    @router.get("/entries/{request_id}")
    def get_entry(request_id: str):
        entry = reader.get_entry(request_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Entry not found")
        return entry

    @router.get("/entries/{request_id}/reveal/{placeholder:path}")
    def reveal_original(request_id: str, placeholder: str):
        entry = reader.get_entry(request_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Entry not found")
        for r in entry.get("redactions", []):
            if r["placeholder"] == placeholder:
                return {"original": r["original"]}
        raise HTTPException(status_code=404, detail="Redaction not found")

    @router.get("/summary")
    def summary():
        return reader.summary()

    @router.post("/allowlist")
    def add_to_allowlist(req: AllowlistRequest):
        allowlist.add_value(req.value, reason=req.reason)
        return {"status": "added", "value": req.value}

    return router
