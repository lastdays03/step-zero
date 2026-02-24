from typing import List, Optional, Dict, Union
from pydantic import BaseModel

class LawItem(BaseModel):
    name: str
    ext: str
    size: str
    summary: str
    path: str
    highlights: Optional[List[str]] = None

class LawChapter(BaseModel):
    title: str
    items: List[LawItem]

class RelatedLaw(BaseModel):
    name: str
    summary: Optional[str] = None

class Highlight(BaseModel):
    id: int
    content: str

class ActionKitItem(BaseModel):
    tag: Optional[str] = None
    name: str
    summary: str
    type: str
    path: str
    relatedLaws: Optional[List[Union[str, RelatedLaw]]] = None
    highlights: Optional[List[Highlight]] = None
    dday: Optional[str] = None

class ActionKitCategory(BaseModel):
    title: str
    items: List[ActionKitItem]


class ActionKitFileUploadResponse(BaseModel):
    item_id: int
    file_id: int
    version: int
    object_key: str
    download_url: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    size_bytes: Optional[int] = None
    checksum: Optional[str] = None
