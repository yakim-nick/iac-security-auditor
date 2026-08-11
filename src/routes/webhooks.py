from __future__ import annotations

import hashlib
import hmac
import logging

from fastapi import APIRouter, Request, HTTPException

from src.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["webhooks"])


@router.post("/github")
async def github_webhook(request: Request):
    """Verify a GitHub webhook signature, then enqueue an audit for the push."""
    body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    if not _is_valid_signature(body, signature):
        raise HTTPException(status_code=403, detail="Invalid signature")

    event = request.headers.get("X-GitHub-Event", "push")
    payload = await request.json()

    logger.info(f"Received webhook: event={event} repo={payload.get('repository', {}).get('full_name')}")

    from src.workers.audit_worker import run_audit
    run_audit.delay(
        repo=payload["repository"]["full_name"],
        ref=payload.get("ref", ""),
        commit_sha=payload.get("after", ""),
    )

    return {"status": "accepted", "event": event}


def _is_valid_signature(body: bytes, signature: str) -> bool:
    """Check the HMAC-SHA256 signature against the shared webhook secret."""
    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(), body, hashlib.sha256
    ).hexdigest()
    # compare_digest runs in constant time, avoiding timing side channels.
    return hmac.compare_digest(signature, expected)
