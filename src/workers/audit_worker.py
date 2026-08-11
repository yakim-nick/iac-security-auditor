from __future__ import annotations

import asyncio
import base64
import logging

import httpx
from celery import Celery, shared_task

from src.config import settings

logger = logging.getLogger(__name__)

# File extensions the auditor knows how to scan.
_AUDITABLE_EXTENSIONS = {".tf", ".yaml", ".yml", ".json"}


def create_celery_app() -> Celery:
    """Create and configure the Celery application after config is loaded."""
    app = Celery("iac_auditor", broker=settings.redis_url, backend=settings.redis_url)
    app.conf.task_serializer = "json"
    app.conf.accept_content = ["json"]
    app.conf.result_expires = 3600
    return app


# Lazy singleton — callers use get_celery_app() to obtain the configured instance.
_celery_app: Celery | None = None


def get_celery_app() -> Celery:
    global _celery_app
    if _celery_app is None:
        _celery_app = create_celery_app()
    return _celery_app


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def run_audit(
    self,
    repo: str,
    ref: str,
    commit_sha: str = "",
    paths: list[str] | None = None,
) -> dict:
    """Celery task: scan a repo ref with the LLM auditor and persist findings."""
    logger.info(f"Starting audit for {repo} @ {ref}")

    # `paths` is accepted for API compatibility but not yet used for filtering.
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_run_audit_async(repo, ref, commit_sha))
    finally:
        loop.close()


async def _run_audit_async(repo: str, ref: str, commit_sha: str) -> dict:
    """Fetch the repo tree, audit every auditable file, and persist the results."""
    from src.services.llm_auditor import LLMAuditor
    from src.models.database import get_pool

    auditor = LLMAuditor()
    pool = await get_pool()

    all_findings: list[dict] = []
    scanned_files = 0

    async with httpx.AsyncClient() as client:
        tree, status_code = await _fetch_repo_tree(client, repo, ref)
        if tree is None:
            logger.error(f"GitHub API error: {status_code}")
            return {"repo": repo, "error": f"GitHub API returned {status_code}"}

        for entry in tree:
            if not _is_auditable_file(entry):
                continue

            raw_content = await _fetch_file_content(client, repo, ref, entry["path"])
            if raw_content is None:
                continue

            findings = await auditor.audit(raw_content, entry["path"])
            for finding in findings:
                finding["file"] = entry["path"]

            all_findings.extend(findings)
            scanned_files += 1

    status = "completed" if not all_findings else "issues_found"
    await _save_audit_result(pool, repo, ref, commit_sha, status, all_findings)

    logger.info(
        f"Audit complete: {scanned_files} files, {len(all_findings)} findings in {repo}"
    )
    return {"repo": repo, "findings_count": len(all_findings), "status": status}


def _github_headers() -> dict:
    """Build the Authorization header used for GitHub API calls."""
    return {"Authorization": f"Bearer {settings.github_token}"}


async def _fetch_repo_tree(
    client: httpx.AsyncClient, repo: str, ref: str
) -> tuple[list[dict] | None, int | None]:
    """Fetch the recursive git tree for a repo ref; (None, status) on failure."""
    url = f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
    resp = await client.get(url, headers=_github_headers())
    if resp.status_code != 200:
        return None, resp.status_code
    return resp.json().get("tree", []), resp.status_code


async def _fetch_file_content(
    client: httpx.AsyncClient, repo: str, ref: str, path: str
) -> str | None:
    """Fetch and base64-decode a file's content from GitHub; None on failure."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}?ref={ref}"
    resp = await client.get(url, headers=_github_headers())
    if resp.status_code != 200:
        return None
    content_data = resp.json()
    return base64.b64decode(content_data["content"]).decode()


def _is_auditable_file(entry: dict) -> bool:
    """Return True if the tree entry is a blob with an auditable file extension."""
    if entry.get("type") != "blob":
        return False
    return any(entry["path"].endswith(ext) for ext in _AUDITABLE_EXTENSIONS)


async def _save_audit_result(
    pool, repo: str, ref: str, commit_sha: str, status: str, findings: list[dict]
) -> None:
    """Persist an audit run and its findings to the audits table."""
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO audits (repo, ref, commit_sha, status, findings) "
            "VALUES ($1, $2, $3, $4, $5::jsonb)",
            repo, ref, commit_sha, status, findings,
        )
