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

class ActionKitItem(BaseModel):
    tag: Optional[str] = None
    name: str
    summary: str
    type: str
    path: str
    relatedLaws: Optional[List[Union[str, RelatedLaw]]] = None
    dday: Optional[str] = None

class ActionKitCategory(BaseModel):
    title: str
    items: List[ActionKitItem]
