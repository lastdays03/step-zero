from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url
from sqlmodel import SQLModel

from alembic import context
from app.core.config import get_settings
from app.models import (  # noqa: F401
    actionkit,
    admin_audit_log,
    announcement,
    audit_log,
    growth_club,
    notification,
    profile,
    refresh_token,
    roadmap,
    roadmap_chat,
    roadmap_template,
    team,
    user,
    user_discipline_history,
)

config = context.config
settings = get_settings()


def _to_alembic_sync_url(database_url: str) -> str:
    """Alembic runs sync engines; convert async drivers to sync ones."""
    url = make_url(database_url)
    backend = url.get_backend_name()
    driver = url.get_driver_name()
    if backend == "postgresql" and driver in {"asyncpg", "psycopg"}:
        return url.set(drivername="postgresql+psycopg2").render_as_string(
            hide_password=False
        )
    if backend == "sqlite" and driver in {"aiosqlite"}:
        return url.set(drivername="sqlite+pysqlite").render_as_string(
            hide_password=False
        )
    return url.render_as_string(hide_password=False)


SYNC_DATABASE_URL = _to_alembic_sync_url(settings.DATABASE_URL)
config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = SQLModel.metadata

# autogenerate에서 수동 생성 인덱스를 삭제 대상으로 감지하지 않도록 설정
MANUAL_INDEXES = {
    "ix_admin_audit_logs_action_target_type_created_at",
    "ix_admin_audit_logs_admin_id_created_at",
}

# LangChain이 직접 관리하는 테이블 (autogenerate에서 제외)
EXCLUDED_TABLES = {
    "langchain_pg_collection",
    "langchain_pg_embedding",
}


def include_name(name, type_, parent_names):
    if type_ == "table" and name in EXCLUDED_TABLES:
        return False
    if type_ == "index" and name in MANUAL_INDEXES:
        return False
    return True


def run_migrations_offline() -> None:
    context.configure(
        url=SYNC_DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        include_name=include_name,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        SYNC_DATABASE_URL,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_name=include_name,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
