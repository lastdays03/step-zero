.PHONY: setup run test migrate-up migrate-revision migrate-check

setup:
	@./scripts/setup_dev.sh

run:
	@.venv/bin/uvicorn app.main:app --reload --port 8000

test:
	@.venv/bin/python -m pytest -q

migrate-up:
	@./scripts/run_alembic.sh upgrade head

migrate-revision:
	@./scripts/run_alembic.sh revision --autogenerate -m "$(m)"

migrate-check:
	@./scripts/check_migrations.sh
