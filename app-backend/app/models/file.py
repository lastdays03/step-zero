from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Index
from sqlmodel import JSON, Column, Field, SQLModel


class File(SQLModel, table=True):
    __tablename__ = "files"
    __table_args__ = (
        Index("ix_files_owner_type_owner_id", "owner_type", "owner_id"),
        Index("ix_files_owner_type_owner_id_is_current", "owner_type", "owner_id", "is_current"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    owner_type: str = Field(index=True)  # "actionkit_item" | "growth_club_post" | "user_profile"
    owner_id: int = Field(index=True)
    category: str = Field(default="document")  # "image" | "file" | "document" | "profile_image"
    object_key: str = Field(unique=True)
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None  # ActionKit용
    version: Optional[int] = Field(default=None, index=True)  # ActionKit용
    is_current: Optional[bool] = Field(default=None, index=True)  # ActionKit용
    kind: Optional[str] = Field(default=None, index=True)  # GrowthClub용: "image" | "file"
    metadata_extra: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False, server_default="{}"))
    uploaded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )
