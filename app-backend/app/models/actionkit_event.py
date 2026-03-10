from datetime import datetime
from enum import Enum
from typing import Optional

import sqlalchemy as sa
from sqlmodel import Field, SQLModel

from app.core.security import utc_now


class ActionKitEventType(str, Enum):
    VIEW = "view"
    DOWNLOAD = "download"
    BULK_DOWNLOAD = "bulk_download"
    SEARCH = "search"
    BOOKMARK = "bookmark"
    DETAIL_VIEW = "detail_view"


class ActionKitEvent(SQLModel, table=True):
    __tablename__ = "actionkit_events"
    __table_args__ = (
        sa.Index("ix_actionkit_events_type_created", "event_type", "created_at"),
        sa.Index("ix_actionkit_events_item_created", "item_id", "created_at"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    event_type: str = Field(index=True)
    item_id: Optional[int] = Field(
        default=None,
        sa_column=sa.Column(
            sa.Integer,
            sa.ForeignKey("actionkit_items.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    user_id: Optional[int] = Field(
        default=None,
        sa_column=sa.Column(
            sa.Integer,
            sa.ForeignKey("user.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    search_query: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now, index=True)
