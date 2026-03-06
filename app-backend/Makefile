.PHONY: setup run worker test test-eval test-eval-t2 test-eval-t3 migrate-up migrate-revision migrate-verify migrate-status rag-bootstrap

setup:
	@./scripts/setup_dev.sh

run:
	@uv run uvicorn app.main:app --reload --port 8000

worker:
	@uv run python -m arq app.workers.roadmap_worker.WorkerSettings

test:
	@uv run pytest -q

test-eval:
	@uv run pytest tests/eval -v -s

test-eval-t2:
	@uv run pytest tests/eval/test_tier2_metrics.py -v -s

test-eval-t3:
	@uv run pytest tests/eval/test_tier3_full.py -v -s

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
