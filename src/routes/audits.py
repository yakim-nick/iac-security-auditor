from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.models.database import get_pool

router = APIRouter(tags=["audits"])


class AuditRequest(BaseModel):
    repo: str
    ref: str = "main"
    paths: list[str] | None = None


@router.post("/scan")
async def trigger_audit(body: AuditRequest):
    from src.workers.audit_worker import run_audit
    task = run_audit.delay(repo=body.repo, ref=body.ref, paths=body.paths)
    return {"task_id": task.id, "repo": body.repo, "status": "queued"}


@router.get("/history")
async def list_audits(limit: int = 20):
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, repo, ref, status, created_at FROM audits ORDER BY created_at DESC LIMIT $1",
            limit,
        )
        return {"audits": [dict(r) for r in rows]}
