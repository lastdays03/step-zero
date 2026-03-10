from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_optional_current_user
from app.core.db import get_session
from app.models.actionkit_event import ActionKitEvent, ActionKitEventType
from app.models.user import AuthenticatedUser

router = APIRouter()


class TrackEventRequest(BaseModel):
    model_config = ConfigDict(use_enum_values=True)

    event_type: ActionKitEventType
    item_id: int | None = None
    search_query: str | None = None


@router.post(
    "/track",
    status_code=204,
    response_class=Response,
    summary="액션키트 이벤트 추적",
    description="사용자 행동(다운로드/조회/검색/북마크 등)을 기록합니다.",
)
async def track_event(
    body: TrackEventRequest,
    session: AsyncSession = Depends(get_session),
    current_user: AuthenticatedUser | None = Depends(get_optional_current_user),
):
    event = ActionKitEvent(
        event_type=body.event_type,
        item_id=body.item_id,
        user_id=current_user.id if current_user else None,
        search_query=body.search_query,
    )
    session.add(event)
    await session.commit()
    return Response(status_code=204)
