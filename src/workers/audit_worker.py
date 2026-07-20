from __future__ import annotations

import asyncio
import base64
import logging

import httpx
from celery import Celery

from src.config import settings

app = Celery("iac_auditor", broker=settings.redis_url, backend=settings.redis_url)
app.conf.task_serializer = "json"
app.conf.accept_content = ["json"]
app.conf.result_expires = 3600

logger = logging.getLogger(__name__)


@app.task(bind=True, max_retries=3, default_retry_delay=30)
def run_audit(
    self,
    repo: str,
    ref: str,
    commit_sha: str = "",
    paths: list[str] | None = None,
) -> dict:
    logger.info(f"Starting audit for {repo} @ {ref}")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    async def _run():
        from src.services.manifest_parser import ManifestParser
        from src.services.llm_auditor import LLMAuditor
        from src.models.database import get_pool

        parser = ManifestParser()
        auditor = LLMAuditor()
        pool = await get_pool()

        all_findings: list[dict] = []
        scanned_files = 0
        allowed_exts = {".tf", ".yaml", ".yml", ".json"}

        url = f"https://api.github.com/repos/{repo}/git/trees/{ref}?recursive=1"
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers={"Authorization": f"Bearer {settings.github_token}"},
            )
            if resp.status_code != 200:
                logger.error(f"GitHub API error: {resp.status_code}")
                return {"repo": repo, "error": f"GitHub API returned {resp.status_code}"}

            tree = resp.json().get("tree", [])
            for entry in tree:
                if entry["type"] != "blob":
                    continue
                if not any(entry["path"].endswith(ext) for ext in allowed_exts):
                    continue

                content_resp = await client.get(
                    f"https://api.github.com/repos/{repo}/contents/{entry['path']}?ref={ref}",
                    headers={"Authorization": f"Bearer {settings.github_token}"},
                )
                if content_resp.status_code != 200:
                    continue

                content_data = content_resp.json()
                raw_content = base64.b64decode(content_data["content"]).decode()
                findings = await auditor.audit(raw_content, entry["path"])
                for finding in findings:
                    finding["file"] = entry["path"]

                all_findings.extend(findings)
                scanned_files += 1

        status = "completed" if not all_findings else "issues_found"
        async with pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO audits (repo, ref, commit_sha, status, findings) "
                "VALUES ($1, $2, $3, $4, $5::jsonb)",
                repo, ref, commit_sha, status, all_findings,
            )

        logger.info(
            f"Audit complete: {scanned_files} files, {len(all_findings)} findings in {repo}"
        )
        return {"repo": repo, "findings_count": len(all_findings), "status": status}

    try:
        return loop.run_until_complete(_run())
    finally:
        loop.close()
