"""team and v2 foundation

Revision ID: 20260213_01
Revises: 
Create Date: 2026-02-13 15:40:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20260213_01"
down_revision = "20260212_00"
branch_labels = None
depends_on = None


def _table_exists(inspector: sa.Inspector, table_name: str) -> bool:
    return inspector.has_table(table_name)


def _column_exists(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(col["name"] == column_name for col in inspector.get_columns(table_name))


def _index_exists(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not inspector.has_table(table_name):
        return False
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    if not _table_exists(inspector, "team"):
        op.create_table(
            "team",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
            sa.Column("deleted_at", sa.DateTime(), nullable=True),
            sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
            sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "team", "ix_team_id"):
        op.create_index("ix_team_id", "team", ["id"], unique=False)
    if not _index_exists(inspector, "team", "ix_team_created_at"):
        op.create_index("ix_team_created_at", "team", ["created_at"], unique=False)

    if not _table_exists(inspector, "teammember"):
        op.create_table(
            "teammember",
            sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
            sa.Column("team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("team.id"), nullable=False),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), nullable=False),
        )
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "teammember", "ix_teammember_team_id"):
        op.create_index("ix_teammember_team_id", "teammember", ["team_id"], unique=False)
    if not _index_exists(inspector, "teammember", "ix_teammember_user_id"):
        op.create_index("ix_teammember_user_id", "teammember", ["user_id"], unique=False)
    if not _index_exists(inspector, "teammember", "ix_teammember_role"):
        op.create_index("ix_teammember_role", "teammember", ["role"], unique=False)
    if not _index_exists(inspector, "teammember", "ix_teammember_created_at"):
        op.create_index("ix_teammember_created_at", "teammember", ["created_at"], unique=False)

    if not _column_exists(inspector, "roadmap", "team_id"):
        op.add_column("roadmap", sa.Column("team_id", postgresql.UUID(as_uuid=True), nullable=True))
        inspector = sa.inspect(bind)
    if not _column_exists(inspector, "roadmap", "deleted_at"):
        op.add_column("roadmap", sa.Column("deleted_at", sa.DateTime(), nullable=True))
        inspector = sa.inspect(bind)
    if not _column_exists(inspector, "roadmap", "created_by"):
        op.add_column("roadmap", sa.Column("created_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True))
        inspector = sa.inspect(bind)
    if not _column_exists(inspector, "roadmap", "updated_by"):
        op.add_column("roadmap", sa.Column("updated_by", sa.Integer(), sa.ForeignKey("user.id"), nullable=True))
        inspector = sa.inspect(bind)
    if not _index_exists(inspector, "roadmap", "ix_roadmap_team_id"):
        op.create_index("ix_roadmap_team_id", "roadmap", ["team_id"], unique=False)

    # 1 user = 1 team backfill
    op.execute(
        """
        INSERT INTO team (id, name, created_at, updated_at, created_by, updated_by)
        SELECT gen_random_uuid(), split_part(u.email, '@', 1) || '''s Team', NOW(), NOW(), u.id, u.id
        FROM "user" u
        WHERE NOT EXISTS (
            SELECT 1 FROM teammember tm WHERE tm.user_id = u.id
        );
        """
    )
    op.execute(
        """
        INSERT INTO teammember (team_id, user_id, role, created_at, updated_at)
        SELECT t.id, t.created_by, 'owner', NOW(), NOW()
        FROM team t
        WHERE t.created_by IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM teammember tm WHERE tm.team_id = t.id AND tm.user_id = t.created_by
        );
        """
    )
    op.execute(
        """
        UPDATE roadmap r
        SET team_id = tm.team_id,
            created_by = r.user_id,
            updated_by = r.user_id
        FROM teammember tm
        WHERE tm.user_id = r.user_id
          AND r.team_id IS NULL;
        """
    )

    if _column_exists(inspector, "roadmap", "team_id"):
        null_team_count = bind.execute(sa.text("SELECT COUNT(*) FROM roadmap WHERE team_id IS NULL")).scalar_one()
        if null_team_count == 0:
            op.alter_column("roadmap", "team_id", nullable=False)

    if _column_exists(inspector, "roadmap", "user_id"):
        op.drop_column("roadmap", "user_id")


def downgrade() -> None:
    op.add_column("roadmap", sa.Column("user_id", sa.Integer(), nullable=True))
    op.execute(
        """
        UPDATE roadmap r
        SET user_id = tm.user_id
        FROM teammember tm
        WHERE tm.team_id = r.team_id
          AND tm.role = 'owner';
        """
    )
    op.alter_column("roadmap", "user_id", nullable=False)

    op.drop_index("ix_roadmap_team_id", table_name="roadmap")
    op.drop_column("roadmap", "updated_by")
    op.drop_column("roadmap", "created_by")
    op.drop_column("roadmap", "deleted_at")
    op.drop_column("roadmap", "team_id")

    op.drop_index("ix_teammember_created_at", table_name="teammember")
    op.drop_index("ix_teammember_role", table_name="teammember")
    op.drop_index("ix_teammember_user_id", table_name="teammember")
    op.drop_index("ix_teammember_team_id", table_name="teammember")
    op.drop_table("teammember")

    op.drop_index("ix_team_created_at", table_name="team")
    op.drop_index("ix_team_id", table_name="team")
    op.drop_table("team")
