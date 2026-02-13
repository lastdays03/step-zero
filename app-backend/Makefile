.PHONY: setup run test

setup:
	@./scripts/setup_dev.sh

run:
	@.venv/bin/uvicorn app.main:app --reload --port 8000

test:
	@.venv/bin/python -m pytest -q
