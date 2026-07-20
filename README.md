# iac-security-auditor

IaC Security Auditor. FastAPI-сервис, который проверяет Infrastructure-as-Code
(Terraform/Kubernetes манифесты) на уязвимости и небезопасные практики с
помощью LLM-аудитора, генерирует Pr-с рекомендациями и поднимает воркеры
для асинхронных проверок.

## Стек
- FastAPI (webhooks + audits routes)
- LLM-аудитор (`src/services/llm_auditor.py`) + парсер манифестов
- Генератор PR (`src/services/pr_generator.py`)
- Worker (`src/workers/audit_worker.py`) для фоновых задач
- Тесты: `tests/test_parser.py`, `tests/conftest.py`

## Запуск
```bash
pip install -e .
uvicorn src.main:app --port 8000
# docker:
docker build -t iac-security-auditor .
docker-compose up
```

## Тестирование
```bash
pytest -q
```

## CI
`.github/workflows/ci.yml` — lint + pytest на каждый push.

## Автор
Nick Yakim — github.com/yakim-nick
