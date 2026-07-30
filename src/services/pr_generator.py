from __future__ import annotations

import logging
import re
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
                    updated_content = self._apply_fix(
                        manifest_content, finding
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

    @staticmethod
    def _apply_fix(manifest_content: str, finding: dict) -> str:
        description = finding.get("description", "")
        remediation = finding.get("remediation", "")
        line_num = finding.get("line", 0)

        if not description and not remediation:
            return manifest_content

        lines = manifest_content.splitlines(keepends=True)

        if isinstance(line_num, int) and line_num > 0 and line_num <= len(lines):
            lines[line_num - 1] = remediation.rstrip("\n\r") + "\n"
            return "".join(lines)

        for i, ln in enumerate(lines):
            if re.search(re.escape(description), ln, re.IGNORECASE):
                lines[i] = remediation.rstrip("\n\r") + "\n"
                return "".join(lines)

        logger.warning(
            "Could not locate description in manifest; falling back to global replace"
        )
        return manifest_content.replace(description, remediation)

    def _build_pr_body(self, findings: list[dict]) -> str:
        lines = ["## Automated Security Audit Findings\n"]
        for f in findings:
            lines.append(f"### {f.get('severity', 'INFO')}: {f.get('rule_id', 'N/A')}")
            lines.append(f"- **Description**: {f.get('description', '')}")
            lines.append(f"- **Remediation**: {f.get('remediation', '')}")
            lines.append("")
        return "\n".join(lines)
