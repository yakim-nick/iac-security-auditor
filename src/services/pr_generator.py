from __future__ import annotations

import logging
from github import Github

from src.config import settings

logger = logging.getLogger(__name__)


class PRGenerator:
    def __init__(self):
        self._gh = Github(settings.github_token)

    async def create_fix_pr(
        self,
        repo_name: str,
        branch: str,
        findings: list[dict],
        manifest_content: str,
        file_path: str,
    ) -> int | None:
        try:
            repo = self._gh.get_repo(repo_name)
            base_branch = repo.get_branch(branch)
            import hashlib
            fingerprint = hashlib.md5(str(findings).encode()).hexdigest()[:8]
            fix_branch = f"{settings.audit_branch_prefix}auto-{fingerprint}"

            try:
                ref = repo.create_git_ref(
                    ref=f"refs/heads/{fix_branch}",
                    sha=base_branch.commit.sha,
                )
            except Exception:
                logger.warning(f"Branch {fix_branch} may already exist")
                return None

            for finding in findings:
                if "remediation" not in finding:
                    continue
                try:
                    contents = repo.get_contents(file_path, ref=branch)
                    updated_content = manifest_content.replace(
                        finding.get("description", ""),
                        finding.get("remediation", ""),
                    )
                    repo.update_file(
                        path=file_path,
                        message=f"fix: {finding.get('rule_id', 'unknown')} - {finding.get('description', '')[:60]}",
                        content=updated_content,
                        sha=contents.sha,
                        branch=fix_branch,
                    )
                except Exception as exc:
                    logger.warning(f"Failed to patch {file_path}: {exc}")

            pr = repo.create_pull(
                title=f"[Security] Auto-fix: {len(findings)} findings in {file_path}",
                body=self._build_pr_body(findings),
                head=fix_branch,
                base=branch,
            )
            logger.info(f"Created PR #{pr.number} in {repo_name}")
            return pr.number
        except Exception as exc:
            logger.error(f"PR creation failed: {exc}", exc_info=True)
            return None

    def _build_pr_body(self, findings: list[dict]) -> str:
        lines = ["## Automated Security Audit Findings\n"]
        for f in findings:
            lines.append(f"### {f.get('severity', 'INFO')}: {f.get('rule_id', 'N/A')}")
            lines.append(f"- **Description**: {f.get('description', '')}")
            lines.append(f"- **Remediation**: {f.get('remediation', '')}")
            lines.append("")
        return "\n".join(lines)
