from __future__ import annotations

import json
import logging
from anthropic import AsyncAnthropic

from src.config import settings

logger = logging.getLogger(__name__)

AUDIT_SYSTEM_PROMPT = """You are an expert IaC security auditor. Given a Terraform or Kubernetes manifest, identify:
1. Security misconfigurations (public S3 buckets, privileged containers, open security groups)
2. CIS benchmark violations
3. PCI DSS compliance violations
4. Cost inefficiencies

For each finding, output:
- severity: CRITICAL|HIGH|MEDIUM|LOW
- rule_id: e.g. CIS-1.2.3
- description: what's wrong
- remediation: how to fix it
- file: the relevant file
- line: approximate line number

Return JSON array: [{"severity": "...", "rule_id": "...", "description": "...", "remediation": "...", "file": "...", "line": 0}]"""


class LLMAuditor:
    def __init__(self):
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def audit(self, manifest_text: str, filename: str) -> list[dict]:
        try:
            response = await self._client.messages.create(
                model=settings.llm_model,
                system=AUDIT_SYSTEM_PROMPT,
                messages=[{
                    "role": "user",
                    "content": f"Audit the following manifest ({filename}):\n\n{manifest_text}",
                }],
                temperature=0.1,
                max_tokens=4000,
            )
            raw = response.content[0].text if response.content else "[]"
            raw = raw.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[1] if "\n" in raw else raw
                raw = raw.rsplit("```", 1)[0] if "```" in raw else raw
            findings = json.loads(raw)
            if isinstance(findings, dict):
                findings = [findings]
            logger.info(f"Audit found {len(findings)} issues in {filename}")
            return findings
        except Exception as exc:
            logger.error(f"Audit failed for {filename}: {exc}", exc_info=True)
            return []
