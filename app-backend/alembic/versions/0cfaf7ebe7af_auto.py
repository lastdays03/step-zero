"""auto

Revision ID: 0cfaf7ebe7af
Revises: 20260220_06
Create Date: 2026-02-21 01:56:52.655884
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0cfaf7ebe7af'
down_revision = '20260220_06'
branch_labels = None
depends_on = None


def _index_exists(conn, index_name):
    result = conn.execute(sa.text(
        "SELECT 1 FROM pg_indexes WHERE indexname = :name"
    ), {"name": index_name})
    return result.scalar() is not None


def _constraint_exists(conn, constraint_name, table_name):
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.table_constraints "
        "WHERE constraint_name = :name AND table_name = :table"
    ), {"name": constraint_name, "table": table_name})
    return result.scalar() is not None


def _fk_exists(conn, table_name, column_name, referred_table):
    result = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.key_column_usage kcu "
        "JOIN information_schema.table_constraints tc ON kcu.constraint_name = tc.constraint_name "
        "WHERE tc.table_name = :table AND kcu.column_name = :col AND tc.constraint_type = 'FOREIGN KEY'"
    ), {"table": table_name, "col": column_name})
    return result.scalar() is not None


def upgrade() -> None:
    conn = op.get_bind()

    # Drop constraints if they exist
    if _constraint_exists(conn, 'uq_actionkit_categories_domain_slug', 'actionkit_categories'):
        op.drop_constraint(op.f('uq_actionkit_categories_domain_slug'), 'actionkit_categories', type_='unique')
    if _constraint_exists(conn, 'uq_actionkit_files_item_id_version', 'actionkit_files'):
        op.drop_constraint(op.f('uq_actionkit_files_item_id_version'), 'actionkit_files', type_='unique')

    # Drop indexes if they exist
    for idx, tbl in [
        ('ix_growthclubcomment_author_id', 'growthclubcomment'),
        ('ix_growthclubcomment_created_at', 'growthclubcomment'),
        ('ix_growthclubcomment_parent_id', 'growthclubcomment'),
        ('ix_growthclubcomment_post_id', 'growthclubcomment'),
        ('ix_growthclubpost_author_id', 'growthclubpost'),
        ('ix_growthclubpost_category', 'growthclubpost'),
        ('ix_growthclubpost_created_at', 'growthclubpost'),
        ('ix_growthclubpost_is_blinded', 'growthclubpost'),
        ('ix_growthclubpostlike_created_at', 'growthclubpostlike'),
        ('ix_growthclubpostlike_user_id', 'growthclubpostlike'),
    ]:
        if _index_exists(conn, idx):
            op.drop_index(op.f(idx), table_name=tbl)

    # Create index if not exists
    if not _index_exists(conn, 'ix_roadmap_created_at'):
        op.create_index(op.f('ix_roadmap_created_at'), 'roadmap', ['created_at'], unique=False)

    # Create foreign key if not exists
    if not _fk_exists(conn, 'roadmap', 'team_id', 'team'):
        op.create_foreign_key(None, 'roadmap', 'team', ['team_id'], ['id'])

    # Drop constraint if exists
    if _constraint_exists(conn, 'roadmap_step_details_roadmap_step_id_key', 'roadmap_step_details'):
        op.drop_constraint(op.f('roadmap_step_details_roadmap_step_id_key'), 'roadmap_step_details', type_='unique')

    op.alter_column('userprofile', 'experiences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('userprofile', 'awards',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)
    op.alter_column('userprofile', 'certificates',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=True)

    if _constraint_exists(conn, 'userprofile_user_id_key', 'userprofile'):
        op.drop_constraint(op.f('userprofile_user_id_key'), 'userprofile', type_='unique')


def downgrade() -> None:
    op.create_unique_constraint(op.f('userprofile_user_id_key'), 'userprofile', ['user_id'], postgresql_nulls_not_distinct=False)
    op.alter_column('userprofile', 'certificates',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('userprofile', 'awards',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.alter_column('userprofile', 'experiences',
               existing_type=postgresql.JSON(astext_type=sa.Text()),
               nullable=False)
    op.create_unique_constraint(op.f('roadmap_step_details_roadmap_step_id_key'), 'roadmap_step_details', ['roadmap_step_id'], postgresql_nulls_not_distinct=False)
    op.drop_constraint(None, 'roadmap', type_='foreignkey')
    op.drop_index(op.f('ix_roadmap_created_at'), table_name='roadmap')
    op.create_index(op.f('ix_growthclubpostlike_user_id'), 'growthclubpostlike', ['user_id'], unique=False)
    op.create_index(op.f('ix_growthclubpostlike_created_at'), 'growthclubpostlike', ['created_at'], unique=False)
    op.create_index(op.f('ix_growthclubpost_is_blinded'), 'growthclubpost', ['is_blinded'], unique=False)
    op.create_index(op.f('ix_growthclubpost_created_at'), 'growthclubpost', ['created_at'], unique=False)
    op.create_index(op.f('ix_growthclubpost_category'), 'growthclubpost', ['category'], unique=False)
    op.create_index(op.f('ix_growthclubpost_author_id'), 'growthclubpost', ['author_id'], unique=False)
    op.create_index(op.f('ix_growthclubcomment_post_id'), 'growthclubcomment', ['post_id'], unique=False)
    op.create_index(op.f('ix_growthclubcomment_parent_id'), 'growthclubcomment', ['parent_id'], unique=False)
    op.create_index(op.f('ix_growthclubcomment_created_at'), 'growthclubcomment', ['created_at'], unique=False)
    op.create_index(op.f('ix_growthclubcomment_author_id'), 'growthclubcomment', ['author_id'], unique=False)
    op.create_unique_constraint(op.f('uq_actionkit_files_item_id_version'), 'actionkit_files', ['item_id', 'version'], postgresql_nulls_not_distinct=False)
    op.create_unique_constraint(op.f('uq_actionkit_categories_domain_slug'), 'actionkit_categories', ['domain', 'slug'], postgresql_nulls_not_distinct=False)
