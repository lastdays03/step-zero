from __future__ import annotations

from typing import Final


class AuditAction:
    USER_STATUS_UPDATED: Final[str] = "user.status.updated"

    ANNOUNCEMENT_CREATED: Final[str] = "announcement.created"
    ANNOUNCEMENT_UPDATED: Final[str] = "announcement.updated"
    ANNOUNCEMENT_DRAFTED: Final[str] = "announcement.drafted"
    ANNOUNCEMENT_PUBLISHED: Final[str] = "announcement.published"
    ANNOUNCEMENT_ARCHIVED: Final[str] = "announcement.archived"

    GROWTH_CLUB_POST_BLINDED: Final[str] = "growth_club.post.blinded"
    GROWTH_CLUB_POST_UNBLINDED: Final[str] = "growth_club.post.unblinded"
    GROWTH_CLUB_POST_DELETED: Final[str] = "growth_club.post.deleted"

    ACTIONKIT_ITEM_STATUS_UPDATED: Final[str] = "actionkit.item.status.updated"


class AuditTargetType:
    USER: Final[str] = "user"
    ANNOUNCEMENT: Final[str] = "announcement"
    GROWTH_CLUB_POST: Final[str] = "growth_club_post"
    ACTIONKIT_ITEM: Final[str] = "actionkit_item"


ALLOWED_AUDIT_ACTIONS: set[str] = {
    AuditAction.USER_STATUS_UPDATED,
    AuditAction.ANNOUNCEMENT_CREATED,
    AuditAction.ANNOUNCEMENT_UPDATED,
    AuditAction.ANNOUNCEMENT_DRAFTED,
    AuditAction.ANNOUNCEMENT_PUBLISHED,
    AuditAction.ANNOUNCEMENT_ARCHIVED,
    AuditAction.GROWTH_CLUB_POST_BLINDED,
    AuditAction.GROWTH_CLUB_POST_UNBLINDED,
    AuditAction.GROWTH_CLUB_POST_DELETED,
    AuditAction.ACTIONKIT_ITEM_STATUS_UPDATED,
}

ALLOWED_AUDIT_TARGET_TYPES: set[str] = {
    AuditTargetType.USER,
    AuditTargetType.ANNOUNCEMENT,
    AuditTargetType.GROWTH_CLUB_POST,
    AuditTargetType.ACTIONKIT_ITEM,
}
