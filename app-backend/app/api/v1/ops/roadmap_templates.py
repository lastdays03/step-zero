from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import deps
from app.api.v1.ops.roadmap_template_schemas import (
    RoadmapTemplateActionCreateRequest,
    RoadmapTemplateActionResponse,
    RoadmapTemplateActionUpdateRequest,
    RoadmapTemplateCreateFromRoadmapRequest,
    RoadmapTemplateDetailResponse,
    RoadmapTemplateResponse,
    RoadmapTemplateStatusUpdateRequest,
    RoadmapTemplateStepResponse,
    RoadmapTemplateSummaryResponse,
    RoadmapTemplateUpdateRequest,
)
from app.core.db import get_session
from app.features.ops.application.roadmap_templates import (
    create_template_action,
    create_template_from_roadmap,
    delete_template,
    delete_template_action,
    get_template_detail,
    get_template_summary,
    list_templates,
    update_template,
    update_template_action,
    update_template_status,
)
from app.models.user import AuthenticatedUser

router = APIRouter(prefix="/roadmap-templates", tags=["ops-roadmap-templates"])


def _serialize_detail(template) -> dict:
    """Convert template with _steps/_actions to response dict."""
    data = {
        "id": template.id,
        "business_type": template.business_type,
        "startup_method": template.startup_method,
        "title": template.title,
        "status": template.status,
        "version": template.version,
        "source_roadmap_id": template.source_roadmap_id,
        "created_by": template.created_by,
        "approved_by": template.approved_by,
        "approved_at": template.approved_at,
        "created_at": template.created_at,
        "updated_at": template.updated_at,
        "steps": [],
    }
    for step in getattr(template, "_steps", []):
        step_data = {
            "id": step.id,
            "template_id": step.template_id,
            "step_order": step.step_order,
            "phase": step.phase,
            "title": step.title,
            "objective": step.objective,
            "estimated_days": step.estimated_days,
            "risk_notes": step.risk_notes,
            "created_at": step.created_at,
            "actions": [],
        }
        for action in getattr(step, "_actions", []):
            step_data["actions"].append({
                "id": action.id,
                "template_step_id": action.template_step_id,
                "action_type": action.action_type,
                "title": action.title,
                "description": action.description,
                "source_url": action.source_url,
                "actionkit_item_id": action.actionkit_item_id,
                "actionkit_file_id": action.actionkit_file_id,
                "sort_order": action.sort_order,
                "metadata_json": action.metadata_json,
                "created_at": action.created_at,
            })
        data["steps"].append(step_data)
    return data


@router.get(
    "/summary",
    response_model=RoadmapTemplateSummaryResponse,
    summary="로드맵 템플릿 통계 조회",
)
async def get_summary_endpoint(
    session: AsyncSession = Depends(get_session),
):
    return await get_template_summary(session)


@router.get(
    "",
    response_model=list[RoadmapTemplateResponse],
    summary="로드맵 템플릿 목록 조회",
)
async def list_templates_endpoint(
    status: str | None = None,
    business_type: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    return await list_templates(session, status=status, business_type=business_type)


@router.get(
    "/{template_id}",
    response_model=RoadmapTemplateDetailResponse,
    summary="로드맵 템플릿 상세 조회",
)
async def get_template_detail_endpoint(
    template_id: int,
    session: AsyncSession = Depends(get_session),
):
    template = await get_template_detail(session, template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return _serialize_detail(template)


@router.post(
    "/from-roadmap",
    response_model=RoadmapTemplateResponse,
    summary="기존 로드맵에서 템플릿 생성",
)
async def create_from_roadmap_endpoint(
    data: RoadmapTemplateCreateFromRoadmapRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
):
    try:
        template = await create_template_from_roadmap(
            session, roadmap_id=data.roadmap_id, user_id=admin_user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return template


@router.patch(
    "/{template_id}",
    response_model=RoadmapTemplateResponse,
    summary="로드맵 템플릿 메타 수정",
)
async def update_template_endpoint(
    template_id: int,
    data: RoadmapTemplateUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        template = await update_template(
            session, template_id, data.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.patch(
    "/{template_id}/status",
    response_model=RoadmapTemplateResponse,
    summary="로드맵 템플릿 상태 변경",
)
async def update_template_status_endpoint(
    template_id: int,
    data: RoadmapTemplateStatusUpdateRequest,
    session: AsyncSession = Depends(get_session),
    admin_user: AuthenticatedUser = Depends(deps.get_current_user),
):
    try:
        template = await update_template_status(
            session,
            template_id,
            new_status=data.new_status,
            admin_id=admin_user.id,
            reason=data.reason,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.delete(
    "/{template_id}",
    summary="로드맵 템플릿 삭제",
)
async def delete_template_endpoint(
    template_id: int,
    session: AsyncSession = Depends(get_session),
):
    try:
        success = await delete_template(session, template_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not success:
        raise HTTPException(status_code=404, detail="Template not found")
    return {"ok": True}


@router.post(
    "/{template_id}/steps/{step_id}/actions",
    response_model=RoadmapTemplateActionResponse,
    summary="템플릿 스텝에 액션 추가",
)
async def create_action_endpoint(
    template_id: int,
    step_id: int,
    data: RoadmapTemplateActionCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        action = await create_template_action(session, step_id, data.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not action:
        raise HTTPException(status_code=404, detail="Step not found")
    return action


@router.patch(
    "/{template_id}/steps/{step_id}/actions/{action_id}",
    response_model=RoadmapTemplateActionResponse,
    summary="템플릿 액션 수정",
)
async def update_action_endpoint(
    template_id: int,
    step_id: int,
    action_id: int,
    data: RoadmapTemplateActionUpdateRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        action = await update_template_action(
            session, action_id, data.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    return action


@router.delete(
    "/{template_id}/steps/{step_id}/actions/{action_id}",
    summary="템플릿 액션 삭제",
)
async def delete_action_endpoint(
    template_id: int,
    step_id: int,
    action_id: int,
    session: AsyncSession = Depends(get_session),
):
    success = await delete_template_action(session, action_id)
    if not success:
        raise HTTPException(status_code=404, detail="Action not found")
    return {"ok": True}
