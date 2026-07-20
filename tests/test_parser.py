from __future__ import annotations

import pytest
from src.services.manifest_parser import ManifestParser


class TestManifestParser:
    def setup_method(self):
        self.parser = ManifestParser()

    def test_parse_yaml(self):
        yaml_content = """
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  containers:
    - name: app
      image: nginx:latest
      securityContext:
        privileged: true
"""
        result = self.parser.parse(yaml_content, "pod.yaml")
        assert result.get("kind") == "Pod"
        assert result["metadata"]["name"] == "test-pod"

    def test_parse_json(self):
        json_content = '{"resource": [{"type": "aws_s3_bucket", "name": "data-lake"}]}'
        result = self.parser.parse(json_content, "main.tf.json")
        assert "resource" in result

    def test_extract_resources_from_terraform(self):
        parsed = {
            "resource": {
                "aws_s3_bucket": {
                    "data-lake": {
                        "bucket": "my-data-lake",
                        "acl": "public-read",
                    }
                },
                "aws_instance": {
                    "web": {
                        "ami": "ami-123",
                        "instance_type": "t2.micro",
                    }
                },
            }
        }
        resources = self.parser.extract_resources(parsed)
        assert len(resources) == 2
        assert resources[0]["type"] == "aws_s3_bucket"
        assert resources[1]["name"] == "web"

    def test_extract_resources_from_kubernetes(self):
        parsed = {
            "apiVersion": "v1",
            "kind": "Deployment",
            "metadata": {"name": "nginx-deploy"},
            "spec": {"replicas": 3},
        }
        resources = self.parser.extract_resources(parsed)
        assert len(resources) == 1
        assert resources[0]["kind"] == "Deployment"
        assert resources[0]["name"] == "nginx-deploy"
