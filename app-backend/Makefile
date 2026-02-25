.PHONY: setup run worker test migrate-up migrate-revision migrate-verify migrate-status rag-bootstrap

setup:
	@./scripts/setup_dev.sh

run:
	@.venv/bin/uvicorn app.main:app --reload --port 8000

worker:
	@.venv/bin/python -m arq app.workers.roadmap_worker.WorkerSettings

test:
	@.venv/bin/python -m pytest -q

migrate-up:
	@./scripts/run_alembic.sh upgrade head

migrate-revision:
	@./scripts/run_alembic.sh revision --autogenerate -m "$(m)"

migrate-verify:
	@./scripts/reset_migrations.sh verify

migrate-status:
	@./scripts/reset_migrations.sh status

rag-bootstrap:
	@./scripts/bootstrap_rag.sh
