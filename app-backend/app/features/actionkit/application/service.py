from collections import defaultdict

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.file import File
from app.repositories.actionkit_repository import ActionKitRepository
from app.repositories.file_repository import FileRepository
from app.services.storage import get_storage_backend

from .file_pipeline import (
    build_object_key,
    detect_mime_type,
)


class ActionKitService:
    def __init__(self, repository: ActionKitRepository):
        self.repository = repository

    @staticmethod
    def _to_public_path(object_key: str | None) -> str:
        if not object_key:
            return ""
        settings = get_settings()
        if settings.STORAGE_BACKEND == "r2":
            storage = get_storage_backend()
            return storage.get_public_url(f"actionkit/{object_key}")
        return f"actionkits/files/{object_key.lstrip('/')}"

    @staticmethod
    def _resolve_category_slug(*, domain: str, category_slug: str) -> str:
        if domain == "laws":
            return f"chapter-{category_slug}"
        return category_slug

    async def _build_law_payload(self) -> dict[str, dict]:
        categories = await self.repository.list_categories(domain="laws")
        if not categories:
            return {}

        category_ids = [
            category.id for category in categories if category.id is not None
        ]
        items = await self.repository.list_items_for_categories(
            domain="laws", category_ids=category_ids
        )
        item_ids = [item.id for item in items if item.id is not None]

        highlights = await self.repository.list_item_highlights(item_ids=item_ids)
        file_repo = FileRepository(self.repository.session)
        files = await file_repo.get_current_files(
            owner_type="actionkit_item", owner_ids=item_ids
        )

        highlights_map: dict[int, list[str]] = defaultdict(list)
        for highlight in highlights:
            highlights_map[highlight.item_id].append(highlight.content)

        file_map = {file.owner_id: file for file in files}

        items_by_category: dict[int, list[dict]] = defaultdict(list)
        for item in items:
            if item.id is None:
                continue
            current_file = file_map.get(item.id)
            path = self._to_public_path(
                current_file.object_key if current_file else None
            )
            items_by_category[item.category_id].append(
                {
                    "id": item.id,
                    "name": item.name,
                    "ext": item.ext or ".pdf",
                    "size": item.size_label or "",
                    "summary": item.summary,
                    "path": path,
                    "highlights": highlights_map.get(item.id) or None,
                }
            )

        payload: dict[str, dict] = {}
        for category in categories:
            if category.id is None:
                continue
            payload[category.slug] = {
                "title": category.title,
                "items": items_by_category.get(category.id, []),
            }
        return payload

    async def _build_kit_payload(self) -> dict[str, dict]:
        categories = await self.repository.list_categories(domain="kits")
        if not categories:
            return {"all": {"title": "전체 액션 키트", "items": []}}

        category_ids = [
            category.id for category in categories if category.id is not None
        ]
        items = await self.repository.list_items_for_categories(
            domain="kits", category_ids=category_ids
        )
        item_ids = [item.id for item in items if item.id is not None]

        related_laws = await self.repository.list_related_laws(item_ids=item_ids)
        file_repo = FileRepository(self.repository.session)
        files = await file_repo.get_current_files(
            owner_type="actionkit_item", owner_ids=item_ids
        )
        highlights = await self.repository.list_item_highlights(item_ids=item_ids)
        checklists = await self.repository.list_checklists(item_ids=item_ids)

        related_map: dict[int, list[dict]] = defaultdict(list)
        for law in related_laws:
            related_map[law.item_id].append(
                {
                    "name": law.law_name,
                    "summary": law.law_summary,
                }
            )

        highlights_map: dict[int, list[dict]] = defaultdict(list)
        for hl in highlights:
            highlights_map[hl.item_id].append(
                {
                    "id": hl.id,
                    "content": hl.content,
                }
            )

        checklists_map: dict[int, list[str]] = defaultdict(list)
        for cl in checklists:
            checklists_map[cl.item_id].append(cl.content)

        file_map = {file.owner_id: file for file in files}

        items_by_category: dict[int, list[dict]] = defaultdict(list)
        for item in items:
            if item.id is None:
                continue
            current_file = file_map.get(item.id)
            path = self._to_public_path(
                current_file.object_key if current_file else None
            )
            items_by_category[item.category_id].append(
                {
                    "id": item.id,
                    "tag": item.tag,
                    "name": item.name,
                    "summary": item.summary,
                    "type": item.file_type or "PDF",
                    "path": path,
                    "relatedLaws": related_map.get(item.id) or None,
                    "highlights": highlights_map.get(item.id) or None,
                    "complianceChecklist": checklists_map.get(item.id) or None,
                    "dday": item.dday,
                }
            )

        payload: dict[str, dict] = {}
        all_items: list[dict] = []
        for category in categories:
            if category.id is None:
                continue
            category_items = items_by_category.get(category.id, [])
            all_items.extend(category_items)
            payload[category.slug] = {
                "title": category.title,
                "items": category_items,
            }

        payload["all"] = {"title": "전체 액션 키트", "items": all_items}
        return payload

    async def list_laws(self) -> dict[str, dict]:
        return await self._build_law_payload()

    async def list_kits(self) -> dict[str, dict]:
        return await self._build_kit_payload()

    async def get_law_chapter(self, chapter_id: str) -> dict | None:
        payload = await self._build_law_payload()
        return payload.get(chapter_id)

    async def get_kit_category(self, category_id: str) -> dict | None:
        payload = await self._build_kit_payload()
        return payload.get(category_id)

    async def upload_item_file(
        self,
        *,
        item_id: int,
        upload_file: UploadFile,
    ) -> dict:
        item_and_category = await self.repository.get_item_with_category(
            item_id=item_id
        )
        if not item_and_category:
            raise ValueError("ActionKit item not found")

        item, category = item_and_category
        file_repo = FileRepository(self.repository.session)
        next_version = await file_repo.get_next_version(
            owner_type="actionkit_item", owner_id=item_id
        )
        settings = get_settings()
        filename = upload_file.filename or f"item-{item_id}-v{next_version}.bin"
        object_key = build_object_key(
            domain=item.domain,
            category_slug=self._resolve_category_slug(
                domain=item.domain, category_slug=category.slug
            ),
            item_id=item_id,
            version=next_version,
            filename=filename,
        )

        mime_type = detect_mime_type(filename, fallback=upload_file.content_type)
        storage = get_storage_backend()
        data = await upload_file.read()
        result = await storage.put(
            f"actionkit/{object_key}", data, content_type=mime_type
        )
        size_bytes, checksum = result.size_bytes, result.checksum

        new_file = await file_repo.create(
            file=File(
                owner_type="actionkit_item",
                owner_id=item_id,
                category="document",
                object_key=object_key,
                original_filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                checksum=checksum,
                version=next_version,
                is_current=False,
            )
        )
        await file_repo.set_current(
            owner_type="actionkit_item",
            owner_id=item_id,
            file_id=new_file.id,  # type: ignore[arg-type]
        )

        await self.repository.commit()

        return {
            "item_id": item_id,
            "file_id": new_file.id,
            "version": new_file.version,
            "object_key": new_file.object_key,
            "download_url": self._to_public_path(new_file.object_key),
            "original_filename": new_file.original_filename,
            "mime_type": new_file.mime_type,
            "size_bytes": new_file.size_bytes,
            "checksum": new_file.checksum,
        }
