from collections import defaultdict
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.models.file import File
from app.repositories.actionkit_repository import ActionKitRepository
from app.repositories.file_repository import FileRepository

from .file_pipeline import (
    build_object_key,
    detect_mime_type,
    save_upload_to_path,
)


class ActionKitService:
    def __init__(self, repository: ActionKitRepository):
        self.repository = repository

    @staticmethod
    def _to_public_path(object_key: str | None) -> str:
        if not object_key:
            return ""
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
        files = await self.repository.list_current_files(item_ids=item_ids)

        highlights_map: dict[int, list[str]] = defaultdict(list)
        for highlight in highlights:
            highlights_map[highlight.item_id].append(highlight.content)

        file_map = {file.item_id: file for file in files}

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
        files = await self.repository.list_current_files(item_ids=item_ids)
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

        file_map = {file.item_id: file for file in files}

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
        next_version = await self.repository.get_next_file_version(item_id=item_id)
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

        destination = Path(settings.ACTIONKIT_STORAGE_PATH) / object_key
        size_bytes, checksum = await save_upload_to_path(
            upload_file, destination=destination
        )
        mime_type = detect_mime_type(filename, fallback=upload_file.content_type)

        await self.repository.clear_current_file_flags(item_id=item_id)
        record = await self.repository.create_file_record(
            item_id=item_id,
            version=next_version,
            object_key=object_key,
            original_filename=filename,
            mime_type=mime_type,
            size_bytes=size_bytes,
            checksum=checksum,
        )

        # 듀얼 라이트: File 모델에도 동일 레코드 생성 (4B-6)
        file_repo = FileRepository(self.repository.session)
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
            "file_id": record.id,
            "version": record.version,
            "object_key": record.object_key,
            "download_url": self._to_public_path(record.object_key),
            "original_filename": record.original_filename,
            "mime_type": record.mime_type,
            "size_bytes": record.size_bytes,
            "checksum": record.checksum,
        }


# TODO(4B-6): ActionKitFile → File 모델 완전 전환 (별도 리팩터 단계)
# - ActionKitRepository.list_current_files → FileRepository.get_current_files(owner_type="actionkit_item")
# - ActionKitRepository.create_file_record → FileRepository.create(File(...))
# - delete 로직에 FileRepository.delete_by_owner("actionkit_item", item_id) 추가
# - 선행 조건: 4B-4 데이터 마이그레이션 + 4B-5 FK 재매핑 완료
