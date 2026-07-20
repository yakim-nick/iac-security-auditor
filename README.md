# iac-security-auditor

An Infrastructure-as-Code security auditor. A FastAPI service that scans IaC
(Terraform / Kubernetes manifests) for misconfigurations and insecure
practices using an LLM auditor, generates pull-request recommendations, and
runs async audits via a worker.

## Stack
- FastAPI (webhooks + audits routes)
- LLM auditor (`src/services/llm_auditor.py`) + manifest parser
- PR generator (`src/services/pr_generator.py`)
- Background worker (`src/workers/audit_worker.py`)
- Tests: `tests/test_parser.py`, `tests/conftest.py`

## Run
```bash
pip install -e .
uvicorn src.main:app --port 8000
# docker:
docker build -t iac-security-auditor .
docker-compose up
```

## Test
```bash
pytest -q
```

## CI
`.github/workflows/ci.yml` — lint + `pytest` on every push, with
least-privilege permissions and pinned action versions.

## Author
Nick Yakim — github.com/yakim-nick
