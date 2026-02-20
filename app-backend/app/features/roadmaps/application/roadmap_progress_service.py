from uuid import UUID

from app.models.roadmap import RoadmapStep, RoadmapStepAction
from app.repositories.roadmap_repository import RoadmapRepository

ALLOWED_STEP_STATUSES = {"PENDING", "IN_PROGRESS", "COMPLETED", "BLOCKED"}


class InvalidRoadmapStepStatusError(ValueError):
    pass


class RoadmapProgressService:
    def __init__(self, roadmap_repo: RoadmapRepository):
        self.roadmap_repo = roadmap_repo

    async def _apply_step_status_transition(
        self,
        *,
        team_id: UUID,
        step: RoadmapStep,
        normalized_status: str,
    ) -> RoadmapStep:
        if normalized_status not in ALLOWED_STEP_STATUSES:
            raise InvalidRoadmapStepStatusError("Unsupported status")

        steps = await self.roadmap_repo.list_steps(step.roadmap_id)
        ordered_steps = sorted(steps, key=lambda s: s.step_order)
        target_idx = next((idx for idx, item in enumerate(ordered_steps) if item.id == step.id), None)
        if target_idx is None:
            raise InvalidRoadmapStepStatusError("Roadmap step sequence not found")

        previous_steps = ordered_steps[:target_idx]
        if normalized_status in {"IN_PROGRESS", "COMPLETED"}:
            if any(prev.status != "COMPLETED" for prev in previous_steps):
                raise InvalidRoadmapStepStatusError("Previous steps must be completed first")

        step.status = normalized_status

        if normalized_status == "COMPLETED":
            active_step_exists = any(
                item.id != step.id and item.status == "IN_PROGRESS" for item in ordered_steps
            )
            if not active_step_exists:
                for next_step in ordered_steps[target_idx + 1 :]:
                    if next_step.status in {"PENDING", "BLOCKED"}:
                        next_step.status = "IN_PROGRESS"
                        break
        return step

    async def update_step_status(
        self,
        *,
        team_id: UUID,
        step_id: int,
        new_status: str,
    ) -> RoadmapStep:
        normalized_status = new_status.strip().upper()
        if normalized_status not in ALLOWED_STEP_STATUSES:
            raise InvalidRoadmapStepStatusError("Unsupported status")

        step = await self.roadmap_repo.get_step_for_team(step_id=step_id, team_id=team_id)
        if not step:
            raise InvalidRoadmapStepStatusError("Roadmap step not found")

        await self._apply_step_status_transition(
            team_id=team_id,
            step=step,
            normalized_status=normalized_status,
        )

        await self.roadmap_repo.commit()
        return step

    async def update_action_completion(
        self,
        *,
        team_id: UUID,
        step_id: int,
        action_id: int,
        completed: bool,
    ) -> RoadmapStepAction:
        step = await self.roadmap_repo.get_step_for_team(step_id=step_id, team_id=team_id)
        if not step:
            raise InvalidRoadmapStepStatusError("Roadmap step not found")

        action = await self.roadmap_repo.get_step_action_for_team(
            step_id=step_id,
            action_id=action_id,
            team_id=team_id,
        )
        if not action:
            raise InvalidRoadmapStepStatusError("Roadmap step action not found")

        metadata = dict(action.metadata_json or {})
        metadata["completed"] = completed
        action.metadata_json = metadata

        checklist_actions = [
            item for item in await self.roadmap_repo.list_step_actions([step_id])
            if item.action_type in {"CHECKLIST", "DOCUMENT"}
        ]
        if checklist_actions:
            all_completed = all(
                bool((item.metadata_json or {}).get("completed") is True)
                for item in checklist_actions
            )
            if all_completed and step.status != "COMPLETED":
                await self._apply_step_status_transition(
                    team_id=team_id,
                    step=step,
                    normalized_status="COMPLETED",
                )
            elif not all_completed and step.status == "COMPLETED":
                step.status = "IN_PROGRESS"

        await self.roadmap_repo.commit()
        return action
