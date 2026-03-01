"""008 feature merge: user suspension, audit log, report rework, checklists, notification extras, roadmap quality

Revision ID: 008_feature_merge
Revises: 7a40266e503b
Create Date: 2026-02-27
"""

import sqlalchemy as sa
import sqlmodel.sql.sqltypes

from alembic import op

revision = "008_feature_merge"
down_revision = "7a40266e503b"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── user table: add suspension / audit columns ──
    op.add_column(
        "user",
        sa.Column(
            "audit_log_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.add_column(
        "user",
        sa.Column(
            "is_suspended",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column("user", sa.Column("suspended_at", sa.DateTime(), nullable=True))
    op.add_column(
        "user",
        sa.Column(
            "suspension_reason", sqlmodel.sql.sqltypes.AutoString(), nullable=True
        ),
    )
    op.create_index("ix_user_is_suspended", "user", ["is_suspended"])

    # ── notification table: add soft-delete and resource tracking ──
    op.add_column(
        "notification",
        sa.Column(
            "is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
    op.add_column("notification", sa.Column("resource_id", sa.Integer(), nullable=True))
    op.create_index("ix_notification_resource_id", "notification", ["resource_id"])

    # ── auditlog table (operational audit, separate from admin_audit_logs) ──
    op.create_table(
        "auditlog",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("action", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("target_type", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("target_id", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("target_author", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("details", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_auditlog_user_id", "auditlog", ["user_id"])
    op.create_index("ix_auditlog_action", "auditlog", ["action"])
    op.create_index("ix_auditlog_target_type", "auditlog", ["target_type"])
    op.create_index("ix_auditlog_target_id", "auditlog", ["target_id"])

    # ── actionkit_checklists table ──
    op.create_table(
        "actionkit_checklists",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("item_id", sa.Integer(), nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["actionkit_items.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_actionkit_checklists_item_id", "actionkit_checklists", ["item_id"]
    )
    op.create_index(
        "ix_actionkit_checklists_sort_order", "actionkit_checklists", ["sort_order"]
    )

    # ── growthclubpostreport: drop old composite-PK table, create new with auto-increment PK ──
    op.drop_table("growthclubpostreport")
    op.create_table(
        "growthclubpostreport",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reporter_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_growthclubpostreport_post_id", "growthclubpostreport", ["post_id"]
    )
    op.create_index(
        "ix_growthclubpostreport_reporter_id", "growthclubpostreport", ["reporter_id"]
    )

    # ── growthclubcommentreport: new table ──
    op.create_table(
        "growthclubcommentreport",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("comment_id", sa.Integer(), nullable=False),
        sa.Column("reporter_id", sa.Integer(), nullable=False),
        sa.Column("reason", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["comment_id"], ["growthclubcomment.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["reporter_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_growthclubcommentreport_comment_id",
        "growthclubcommentreport",
        ["comment_id"],
    )
    op.create_index(
        "ix_growthclubcommentreport_reporter_id",
        "growthclubcommentreport",
        ["reporter_id"],
    )

    # ── growthclubcomment: add CASCADE to foreign keys ──
    op.drop_constraint(
        "growthclubcomment_post_id_fkey", "growthclubcomment", type_="foreignkey"
    )
    op.create_foreign_key(
        "growthclubcomment_post_id_fkey",
        "growthclubcomment",
        "growthclubpost",
        ["post_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.drop_constraint(
        "growthclubcomment_parent_id_fkey", "growthclubcomment", type_="foreignkey"
    )
    op.create_foreign_key(
        "growthclubcomment_parent_id_fkey",
        "growthclubcomment",
        "growthclubcomment",
        ["parent_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # ── roadmap_step_details: add quality metadata columns ──
    op.add_column(
        "roadmap_step_details", sa.Column("source_count", sa.Integer(), nullable=True)
    )
    op.add_column(
        "roadmap_step_details", sa.Column("has_fallback", sa.Boolean(), nullable=True)
    )
    op.add_column(
        "roadmap_step_details",
        sa.Column("mapping_source", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )


def downgrade() -> None:
    # ── roadmap_step_details ──
    op.drop_column("roadmap_step_details", "mapping_source")
    op.drop_column("roadmap_step_details", "has_fallback")
    op.drop_column("roadmap_step_details", "source_count")

    # ── growthclubcomment: revert CASCADE ──
    op.drop_constraint(
        "growthclubcomment_parent_id_fkey", "growthclubcomment", type_="foreignkey"
    )
    op.create_foreign_key(
        "growthclubcomment_parent_id_fkey",
        "growthclubcomment",
        "growthclubcomment",
        ["parent_id"],
        ["id"],
    )
    op.drop_constraint(
        "growthclubcomment_post_id_fkey", "growthclubcomment", type_="foreignkey"
    )
    op.create_foreign_key(
        "growthclubcomment_post_id_fkey",
        "growthclubcomment",
        "growthclubpost",
        ["post_id"],
        ["id"],
    )

    # ── growthclubcommentreport ──
    op.drop_index("ix_growthclubcommentreport_reporter_id", "growthclubcommentreport")
    op.drop_index("ix_growthclubcommentreport_comment_id", "growthclubcommentreport")
    op.drop_table("growthclubcommentreport")

    # ── growthclubpostreport: restore old composite-PK version ──
    op.drop_index("ix_growthclubpostreport_reporter_id", "growthclubpostreport")
    op.drop_index("ix_growthclubpostreport_post_id", "growthclubpostreport")
    op.drop_table("growthclubpostreport")
    op.create_table(
        "growthclubpostreport",
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["growthclubpost.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"]),
        sa.PrimaryKeyConstraint("post_id", "user_id"),
    )

    # ── actionkit_checklists ──
    op.drop_index("ix_actionkit_checklists_sort_order", "actionkit_checklists")
    op.drop_index("ix_actionkit_checklists_item_id", "actionkit_checklists")
    op.drop_table("actionkit_checklists")

    # ── auditlog ──
    op.drop_index("ix_auditlog_target_id", "auditlog")
    op.drop_index("ix_auditlog_target_type", "auditlog")
    op.drop_index("ix_auditlog_action", "auditlog")
    op.drop_index("ix_auditlog_user_id", "auditlog")
    op.drop_table("auditlog")

    # ── notification ──
    op.drop_index("ix_notification_resource_id", "notification")
    op.drop_column("notification", "resource_id")
    op.drop_column("notification", "is_deleted")

    # ── user ──
    op.drop_index("ix_user_is_suspended", "user")
    op.drop_column("user", "suspension_reason")
    op.drop_column("user", "suspended_at")
    op.drop_column("user", "is_suspended")
    op.drop_column("user", "audit_log_reason")
