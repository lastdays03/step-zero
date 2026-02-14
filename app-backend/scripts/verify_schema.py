#!/usr/bin/env python3
from __future__ import annotations

from sqlalchemy import create_engine, inspect

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    engine = create_engine(sync_url)
    inspector = inspect(engine)

    required_tables = {"user", "team", "teammember", "roadmap", "roadmapstep"}
    existing_tables = set(inspector.get_table_names())
    missing_tables = sorted(required_tables - existing_tables)
    if missing_tables:
        raise SystemExit(f"Missing tables after migration: {missing_tables}")

    roadmap_columns = {column["name"] for column in inspector.get_columns("roadmap")}
    required_roadmap_columns = {
        "id",
        "team_id",
        "title",
        "business_type",
        "location",
        "description",
        "created_at",
        "updated_at",
        "deleted_at",
        "created_by",
        "updated_by",
    }
    missing_roadmap_columns = sorted(required_roadmap_columns - roadmap_columns)
    if missing_roadmap_columns:
        raise SystemExit(f"Missing roadmap columns: {missing_roadmap_columns}")

    if "user_id" in roadmap_columns:
        raise SystemExit("Deprecated column roadmap.user_id still exists")

    print("Schema verification passed")


if __name__ == "__main__":
    main()
