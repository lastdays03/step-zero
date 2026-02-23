"""ensure pgvector extension is enabled

Revision ID: 20260223_01
Revises: 20260220_06
Create Date: 2026-02-23 10:30:00.000000
"""

from alembic import op


revision = "20260223_01"
down_revision = "20260220_06"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Required for RAG vector storage (langchain_postgres / PGVector).
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    # Intentionally no-op.
    # Dropping extension can break existing vector columns/indexes and shared DBs.
    pass
