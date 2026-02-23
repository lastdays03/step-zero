from typing import TypedDict


class OpsMenuItem(TypedDict):
    key: str
    path: str
    label: str


class OpsOverview(TypedDict):
    menus: list[OpsMenuItem]


def get_overview() -> OpsOverview:
    return {
        "menus": [
            {"key": "reports", "path": "/ops/reports", "label": "운영 리포트"},
            {"key": "users", "path": "/ops/users", "label": "사용자 관리"},
            {"key": "growth-club", "path": "/ops/growth-club", "label": "그로스 클럽 관리"},
            {"key": "actionkit", "path": "/ops/actionkit", "label": "액션 키트 관리"},
            {"key": "announcements", "path": "/ops/announcements", "label": "공지 관리"},
            {"key": "audit-logs", "path": "/ops/audit-logs", "label": "운영 감사로그"},
        ]
    }
