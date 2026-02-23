from typing import TypedDict


class AnnouncementItem(TypedDict):
    id: str
    title: str
    status: str


class AnnouncementList(TypedDict):
    items: list[AnnouncementItem]


def list_announcements() -> AnnouncementList:
    # TODO: connect to announcements repository
    return {"items": []}
