from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import List, Optional

class ActionKitFileResponse(BaseModel):
    id: int
    version: int
    original_filename: str | None
    mime_type: str | None
    size_bytes: int | None
    is_current: bool
    uploaded_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RelatedLawResponse(BaseModel):
    id: int
    law_name: str
    law_summary: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)

class ActionKitItemHighlightResponse(BaseModel):
    id: int
    content: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)

class ActionKitChecklistResponse(BaseModel):
    id: int
    content: str
    sort_order: int

    model_config = ConfigDict(from_attributes=True)

class ActionKitItemResponse(BaseModel):
    id: int
    domain: str
    category_id: int
    name: str
    summary: str
    tag: str | None
    ext: str | None
    size_label: str | None
    file_type: str | None
    dday: str | None
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    files: List[ActionKitFileResponse] = []
    related_laws: List[RelatedLawResponse] = []
    highlights: List[ActionKitItemHighlightResponse] = []
    checklists: List[ActionKitChecklistResponse] = []

    model_config = ConfigDict(from_attributes=True)
class ActionKitCategoryCreateRequest(BaseModel):
    domain: str = "kits"
    slug: str
    title: str
    sort_order: int = 0
    is_active: bool = True

class ActionKitCategoryUpdateRequest(BaseModel):
    slug: str | None = None
    title: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None

class ActionKitCategoryResponse(BaseModel):
    id: int
    domain: str
    slug: str
    title: str
    sort_order: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class ActionKitItemCreateRequest(BaseModel):
    domain: str
    category_id: int
    name: str
    summary: str
    tag: str | None = None
    ext: str | None = None
    size_label: str | None = None
    file_type: str | None = None
    dday: str | None = None
    sort_order: int = 0
    is_active: bool = True

class ActionKitItemUpdateRequest(BaseModel):
    category_id: int | None = None
    name: str | None = None
    summary: str | None = None
    tag: str | None = None
    ext: str | None = None
    size_label: str | None = None
    file_type: str | None = None
    dday: str | None = None
    sort_order: int | None = None
    is_active: bool | None = None
