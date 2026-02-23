from typing import TypedDict


class AuditLogItem(TypedDict):
    id: str
    actor: str
    action: str
    created_at: str


class AuditLogList(TypedDict):
    items: list[AuditLogItem]


def list_audit_logs() -> AuditLogList:
    # TODO: connect to audit log repository
    return {"items": []}
