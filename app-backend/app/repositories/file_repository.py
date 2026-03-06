import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.file import File


class FileRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, *, file: File) -> File:
        self.session.add(file)
        await self.session.flush()
        return file

    async def get_by_id(self, file_id: int) -> File | None:
        stmt = select(File).where(File.id == file_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_key(self, object_key: str) -> File | None:
        stmt = select(File).where(File.object_key == object_key)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_owner(
        self, *, owner_type: str, owner_id: int
    ) -> list[File]:
        stmt = (
            select(File)
            .where(File.owner_type == owner_type, File.owner_id == owner_id)
            .order_by(File.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_current_files(
        self, *, owner_type: str, owner_ids: list[int]
    ) -> list[File]:
        """ActionKit용: is_current=True인 파일들 조회"""
        if not owner_ids:
            return []
        stmt = (
            select(File)
            .where(
                File.owner_type == owner_type,
                File.owner_id.in_(owner_ids),
                File.is_current.is_(True),
            )
            .order_by(File.version.desc(), File.id.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_id(self, file_id: int) -> bool:
        stmt = select(File).where(File.id == file_id)
        result = await self.session.execute(stmt)
        file = result.scalar_one_or_none()
        if file:
            await self.session.delete(file)
            return True
        return False

    async def delete_by_owner(
        self, *, owner_type: str, owner_id: int
    ) -> int:
        """Cascade Delete 대체: 소유자의 모든 파일 레코드 삭제. 삭제된 수 반환."""
        stmt = (
            sa.delete(File)
            .where(File.owner_type == owner_type, File.owner_id == owner_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount

    async def set_current(
        self, *, owner_type: str, owner_id: int, file_id: int
    ) -> None:
        """ActionKit용: 해당 owner의 모든 파일을 is_current=False로 변경 후, 지정 파일만 True"""
        # 전체 False
        stmt = (
            sa.update(File)
            .where(
                File.owner_type == owner_type,
                File.owner_id == owner_id,
                File.is_current.is_(True),
            )
            .values(is_current=False)
        )
        await self.session.execute(stmt)
        # 지정 파일 True
        stmt2 = (
            sa.update(File)
            .where(File.id == file_id)
            .values(is_current=True)
        )
        await self.session.execute(stmt2)

    async def get_next_version(
        self, *, owner_type: str, owner_id: int
    ) -> int:
        """ActionKit용: 다음 버전 번호"""
        stmt = select(sa.func.max(File.version)).where(
            File.owner_type == owner_type, File.owner_id == owner_id
        )
        result = await self.session.execute(stmt)
        max_version = result.scalar_one_or_none() or 0
        return int(max_version) + 1

    async def commit(self) -> None:
        await self.session.commit()
