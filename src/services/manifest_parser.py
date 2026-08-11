from __future__ import annotations

import yaml
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ManifestParser:
    """Parse IaC manifests and flatten them into resource descriptors."""

    @staticmethod
    def parse(content: str, filename: str) -> dict:
        """Parse a manifest into a dict, dispatching on the file extension."""
        ext = Path(filename).suffix.lower()
        if ext in (".yaml", ".yml"):
            return yaml.safe_load(content) or {}
        elif ext == ".json":
            return json.loads(content)
        elif ext == ".tf":
            # Terraform HCL has no stdlib parser; keep raw text for the LLM.
            return {"type": "terraform", "content": content}
        elif ext in (".py",):
            # CDK (Python) manifests are audited as raw source.
            return {"type": "cdk", "content": content}
        else:
            return {"type": "unknown", "content": content}

    @staticmethod
    def extract_resources(parsed: dict) -> list[dict]:
        """Flatten a parsed manifest into a list of resource descriptors."""
        resources = []
        resources.extend(ManifestParser._extract_terraform_resources(parsed))
        resources.extend(ManifestParser._extract_kubernetes_resources(parsed))
        return resources

    @staticmethod
    def _extract_terraform_resources(parsed: dict) -> list[dict]:
        """Flatten Terraform's nested resource blocks into resource descriptors."""
        resources = []
        for resource_type, instances in parsed.get("resource", {}).items():
            for name, config in instances.items():
                resources.append({"type": resource_type, "name": name, "config": config})
        return resources

    @staticmethod
    def _extract_kubernetes_resources(parsed: dict) -> list[dict]:
        """Wrap a single Kubernetes manifest as one resource descriptor."""
        if "kind" not in parsed:
            return []
        return [{
            "type": "kubernetes",
            "kind": parsed.get("kind"),
            "name": parsed.get("metadata", {}).get("name"),
            "config": parsed,
        }]
