from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class ActionKitCategory(SQLModel, table=True):
    __tablename__ = "actionkit_categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(index=True)  # laws | kits
    slug: str = Field(index=True)
    title: str
    sort_order: int = Field(default=0, index=True)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    items: list["ActionKitItem"] = Relationship(back_populates="category")


class ActionKitItem(SQLModel, table=True):
    __tablename__ = "actionkit_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(index=True)  # laws | kits
    category_id: int = Field(foreign_key="actionkit_categories.id", index=True)
    name: str
    summary: str
    tag: str | None = None
    ext: str | None = None
    size_label: str | None = None
    file_type: str | None = None
    dday: str | None = None
    sort_order: int = Field(default=0, index=True)
    is_active: bool = Field(default=True, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    category: ActionKitCategory = Relationship(back_populates="items")
    files: list["ActionKitFile"] = Relationship(back_populates="item", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    highlights: list["ActionKitItemHighlight"] = Relationship(back_populates="item", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    related_laws: list["ActionKitRelatedLaw"] = Relationship(back_populates="item", sa_relationship_kwargs={"cascade": "all, delete-orphan"})


class ActionKitItemHighlight(SQLModel, table=True):
    __tablename__ = "actionkit_item_highlights"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="actionkit_items.id", index=True)
    content: str
    sort_order: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    item: ActionKitItem = Relationship(back_populates="highlights")


class ActionKitRelatedLaw(SQLModel, table=True):
    __tablename__ = "actionkit_related_laws"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="actionkit_items.id", index=True)
    law_name: str
    law_summary: str | None = None
    sort_order: int = Field(default=0, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    item: ActionKitItem = Relationship(back_populates="related_laws")


class ActionKitFile(SQLModel, table=True):
    __tablename__ = "actionkit_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    item_id: int = Field(foreign_key="actionkit_items.id", index=True)
    version: int = Field(default=1, index=True)
    object_key: str
    original_filename: str | None = None
    mime_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    is_current: bool = Field(default=True, index=True)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    item: ActionKitItem = Relationship(back_populates="files")
