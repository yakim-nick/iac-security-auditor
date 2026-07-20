from __future__ import annotations

import yaml
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class ManifestParser:
    @staticmethod
    def parse(content: str, filename: str) -> dict:
        ext = Path(filename).suffix.lower()
        if ext in (".yaml", ".yml"):
            return yaml.safe_load(content) or {}
        elif ext == ".json":
            return json.loads(content)
        elif ext == ".tf":
            return {"type": "terraform", "content": content}
        elif ext in (".py",):
            return {"type": "cdk", "content": content}
        else:
            return {"type": "unknown", "content": content}

    @staticmethod
    def extract_resources(parsed: dict) -> list[dict]:
        resources = []
        if "resource" in parsed:
            for resource_type, instances in parsed["resource"].items():
                for name, config in instances.items():
                    resources.append({"type": resource_type, "name": name, "config": config})
        if "kind" in parsed:
            resources.append({
                "type": "kubernetes",
                "kind": parsed.get("kind"),
                "name": parsed.get("metadata", {}).get("name"),
                "config": parsed,
            })
        return resources
