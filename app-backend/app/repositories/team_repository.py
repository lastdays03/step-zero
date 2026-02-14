from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team, TeamMember


class TeamRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_default_team_for_user(self, user_id: int, user_email: str) -> Team:
        team = Team(name=f"{user_email.split('@')[0]}'s Team", created_by=user_id, updated_by=user_id)
        self.session.add(team)
        await self.session.flush()

        membership = TeamMember(team_id=team.id, user_id=user_id, role="owner")
        self.session.add(membership)
        await self.session.commit()
        await self.session.refresh(team)
        return team

    async def get_primary_team_for_user(self, user_id: int) -> Team | None:
        stmt = (
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
            .order_by(TeamMember.id.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(self, user_id: int) -> list[Team]:
        stmt = (
            select(Team)
            .join(TeamMember, TeamMember.team_id == Team.id)
            .where(TeamMember.user_id == user_id)
            .order_by(TeamMember.id.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
