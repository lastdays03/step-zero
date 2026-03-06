from __future__ import annotations

from datetime import datetime
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.ops.application.audit_logs import record_admin_audit_log
from app.features.ops.application.audit_logs.constants import (
    AuditAction,
    AuditTargetType,
)
from app.models.file import File
from app.services.storage import get_storage_backend


def _mime_group_case():
    return sa.case(
        (File.mime_type.like("image/%"), "image"),
        (
            sa.or_(
                File.mime_type.like("application/pdf%"),
                File.mime_type.like("application/msword%"),
                File.mime_type.like("application/vnd.openxmlformats%"),
                File.mime_type.like("text/%"),
            ),
            "document",
        ),
        else_="other",
    )


class OpsFilesService:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def list_files(
        self,
        *,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_dir: str = "desc",
        owner_type: str | None = None,
        mime_group: str | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        search: str | None = None,
    ) -> dict[str, Any]:
        filters: list[Any] = []

        if owner_type:
            filters.append(File.owner_type == owner_type)
        if date_from:
            filters.append(File.uploaded_at >= date_from)
        if date_to:
            filters.append(File.uploaded_at <= date_to)
        if search:
            filters.append(File.original_filename.ilike(f"%{search}%"))
        if mime_group:
            if mime_group == "image":
                filters.append(File.mime_type.like("image/%"))
            elif mime_group == "document":
                filters.append(
                    sa.or_(
                        File.mime_type.like("application/pdf%"),
                        File.mime_type.like("application/msword%"),
                        File.mime_type.like("application/vnd.openxmlformats%"),
                        File.mime_type.like("text/%"),
                    )
                )
            elif mime_group == "other":
                filters.append(
                    ~sa.or_(
                        File.mime_type.like("image/%"),
                        File.mime_type.like("application/pdf%"),
                        File.mime_type.like("application/msword%"),
                        File.mime_type.like("application/vnd.openxmlformats%"),
                        File.mime_type.like("text/%"),
                    )
                )

        # Total count
        count_stmt = sa.select(sa.func.count()).select_from(File)
        if filters:
            count_stmt = count_stmt.where(*filters)
        total = int((await self._session.execute(count_stmt)).scalar_one())

        # Sorting
        sort_column_map = {
            "created_at": File.created_at,
            "uploaded_at": File.uploaded_at,
            "size_bytes": File.size_bytes,
            "original_filename": File.original_filename,
        }
        sort_col = sort_column_map.get(sort_by, File.created_at)
        order = sort_col.desc() if sort_dir == "desc" else sort_col.asc()

        # Data query
        offset = (page - 1) * page_size
        data_stmt = sa.select(File)
        if filters:
            data_stmt = data_stmt.where(*filters)
        data_stmt = data_stmt.order_by(order, File.id.desc()).offset(offset).limit(page_size)
        rows = (await self._session.execute(data_stmt)).scalars().all()

        storage = get_storage_backend()
        data = []
        for f in rows:
            item: dict[str, Any] = {
                "id": f.id,
                "owner_type": f.owner_type,
                "owner_id": f.owner_id,
                "category": f.category,
                "object_key": f.object_key,
                "original_filename": f.original_filename,
                "mime_type": f.mime_type,
                "size_bytes": f.size_bytes,
                "kind": f.kind,
                "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else None,
                "public_url": storage.get_public_url(f.object_key),
            }
            data.append(item)

        return {"data": data, "total": total, "page": page, "page_size": page_size}

    async def get_stats(self) -> dict[str, Any]:
        # Total count + total bytes
        total_stmt = sa.select(
            sa.func.count().label("total_files"),
            sa.func.coalesce(sa.func.sum(File.size_bytes), 0).label("total_bytes"),
        ).select_from(File)
        row = (await self._session.execute(total_stmt)).one()
        total_files = int(row.total_files)
        total_bytes = int(row.total_bytes)

        # By owner_type
        owner_stmt = (
            sa.select(
                File.owner_type,
                sa.func.count().label("count"),
                sa.func.coalesce(sa.func.sum(File.size_bytes), 0).label("bytes"),
            )
            .select_from(File)
            .group_by(File.owner_type)
        )
        owner_rows = (await self._session.execute(owner_stmt)).all()
        by_owner_type = [
            {"owner_type": r.owner_type, "count": int(r.count), "bytes": int(r.bytes)}
            for r in owner_rows
        ]

        # By mime_group
        mime_case = _mime_group_case()
        mime_stmt = (
            sa.select(
                mime_case.label("mime_group"),
                sa.func.count().label("count"),
                sa.func.coalesce(sa.func.sum(File.size_bytes), 0).label("bytes"),
            )
            .select_from(File)
            .group_by(mime_case)
        )
        mime_rows = (await self._session.execute(mime_stmt)).all()
        by_mime_group = [
            {"mime_group": r.mime_group, "count": int(r.count), "bytes": int(r.bytes)}
            for r in mime_rows
        ]

        return {
            "total_files": total_files,
            "total_bytes": total_bytes,
            "by_owner_type": by_owner_type,
            "by_mime_group": by_mime_group,
        }

    async def delete_file(self, file_id: int, *, admin_id: int) -> bool:
        stmt = sa.select(File).where(File.id == file_id)
        result = await self._session.execute(stmt)
        file = result.scalar_one_or_none()
        if not file:
            return False

        storage = get_storage_backend()
        storage_ok = await storage.delete(file.object_key)
        if not storage_ok:
            return False

        meta = {
            "filename": file.original_filename,
            "object_key": file.object_key,
            "size_bytes": file.size_bytes,
        }

        await self._session.delete(file)
        await self._session.flush()

        await record_admin_audit_log(
            self._session,
            admin_id=admin_id,
            action=AuditAction.FILE_DELETED,
            target_type=AuditTargetType.FILE,
            target_id=str(file_id),
            meta=meta,
        )

        return True

    async def delete_files(
        self, file_ids: list[int], *, admin_id: int
    ) -> dict[str, int]:
        if not file_ids:
            return {"deleted": 0, "failed": 0}

        stmt = sa.select(File).where(File.id.in_(file_ids))
        result = await self._session.execute(stmt)
        files = {f.id: f for f in result.scalars().all()}

        storage = get_storage_backend()
        success_ids: list[int] = []
        failed_ids: list[int] = []

        for fid in file_ids:
            file = files.get(fid)
            if not file:
                failed_ids.append(fid)
                continue
            ok = await storage.delete(file.object_key)
            if ok:
                success_ids.append(fid)
            else:
                failed_ids.append(fid)

        if success_ids:
            del_stmt = sa.delete(File).where(File.id.in_(success_ids))
            await self._session.execute(del_stmt)
            await self._session.flush()

        await record_admin_audit_log(
            self._session,
            admin_id=admin_id,
            action=AuditAction.FILE_BULK_DELETED,
            target_type=AuditTargetType.FILE,
            meta={
                "deleted_count": len(success_ids),
                "failed_count": len(failed_ids),
                "file_ids": success_ids,
                "failed_ids": failed_ids,
            },
        )

        return {"deleted": len(success_ids), "failed": len(failed_ids)}
