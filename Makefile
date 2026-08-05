.PHONY: install run worker test lint docker

install:
	pip install -r requirements.txt

run:
	uvicorn src.main:app --reload --port 8000

worker:
	celery -A src.workers.audit_worker worker --loglevel=info

test:
	pytest tests/ -v

lint:
	ruff check .

docker:
	docker compose up --build
