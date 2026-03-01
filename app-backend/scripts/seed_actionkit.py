#!/usr/bin/env python3
from __future__ import annotations

import asyncio
import hashlib
import mimetypes
import shutil
from datetime import datetime, timezone
from pathlib import Path

from sqlmodel import select

from app.core.config import get_settings
from app.core.db import async_session


def detect_mime_type(filename: str, fallback: str | None = None) -> str:
    guessed, _ = mimetypes.guess_type(filename)
    return guessed or fallback or "application/octet-stream"


def file_checksum(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


from app.models.actionkit import (
    ActionKitCategory,
    ActionKitFile,
    ActionKitItem,
    ActionKitItemHighlight,
    ActionKitRelatedLaw,
)
from scripts.seeds.actionkit_seed_source import ACTION_KIT_DATA, LAW_DATA


def _to_object_key(
    *, domain: str, category_slug: str, item_id: int, filename: str
) -> str:
    return f"{domain}/{category_slug}/{item_id}/v1/{filename}"


def _strip_prefix(path: str) -> str:
    normalized = path.strip().lstrip("/")
    if normalized.startswith("actionkits/files/"):
        return normalized[len("actionkits/files/") :]
    return normalized


def _resolve_legacy_source(*, backend_root: Path, original_path: str) -> Path | None:
    relative = _strip_prefix(original_path)
    storage_root = backend_root / "storage" / "actionkit"
    direct = storage_root / relative
    if direct.exists():
        return direct

    fallback = storage_root / Path(relative).name
    if fallback.exists():
        return fallback

    return None


async def seed() -> None:
    settings = get_settings()
    backend_root = Path(__file__).resolve().parents[1]
    storage_root = settings.ACTIONKIT_STORAGE_PATH
    storage_root.mkdir(parents=True, exist_ok=True)

    async with async_session() as session:
        existing = await session.execute(select(ActionKitCategory.id).limit(1))
        if existing.first():
            print("[seed_actionkit] actionkit data already exists. skipping.")
            return

        now = datetime.now(timezone.utc)

        law_categories: dict[str, ActionKitCategory] = {}
        for sort_order, (slug, chapter) in enumerate(LAW_DATA.items(), start=1):
            category = ActionKitCategory(
                domain="laws",
                slug=slug,
                title=chapter["title"],
                sort_order=sort_order,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(category)
            await session.flush()
            law_categories[slug] = category

        kit_categories: dict[str, ActionKitCategory] = {}
        kit_entries = [
            (slug, cat) for slug, cat in ACTION_KIT_DATA.items() if slug != "all"
        ]
        for sort_order, (slug, category_data) in enumerate(kit_entries, start=1):
            category = ActionKitCategory(
                domain="kits",
                slug=slug,
                title=category_data["title"],
                sort_order=sort_order,
                is_active=True,
                created_at=now,
                updated_at=now,
            )
            session.add(category)
            await session.flush()
            kit_categories[slug] = category

        for chapter_slug, chapter in LAW_DATA.items():
            category = law_categories[chapter_slug]
            for item_sort_order, law_item in enumerate(chapter["items"], start=1):
                item = ActionKitItem(
                    domain="laws",
                    category_id=category.id,
                    name=law_item["name"],
                    summary=law_item["summary"],
                    ext=law_item.get("ext"),
                    size_label=law_item.get("size"),
                    file_type=(law_item.get("ext") or "").replace(".", "").upper()
                    or "PDF",
                    sort_order=item_sort_order,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                session.add(item)
                await session.flush()

                for h_idx, highlight in enumerate(
                    law_item.get("highlights", []), start=1
                ):
                    session.add(
                        ActionKitItemHighlight(
                            item_id=item.id,
                            content=highlight,
                            sort_order=h_idx,
                            created_at=now,
                        )
                    )

                source_path = _resolve_legacy_source(
                    backend_root=backend_root,
                    original_path=law_item.get("path", ""),
                )
                filename = (
                    Path(_strip_prefix(law_item.get("path", ""))).name
                    or f"law-{item.id}.pdf"
                )
                object_key = _to_object_key(
                    domain="laws",
                    category_slug=f"chapter-{chapter_slug}",
                    item_id=item.id,
                    filename=filename,
                )
                target_path = storage_root / object_key
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if source_path and source_path.exists() and not target_path.exists():
                    shutil.copy2(source_path, target_path)
                size_bytes = (
                    target_path.stat().st_size if target_path.exists() else None
                )
                checksum = file_checksum(target_path) if target_path.exists() else None
                mime_type = detect_mime_type(filename)

                session.add(
                    ActionKitFile(
                        item_id=item.id,
                        version=1,
                        object_key=object_key,
                        original_filename=filename,
                        mime_type=mime_type,
                        size_bytes=size_bytes,
                        checksum=checksum,
                        is_current=True,
                        uploaded_at=now,
                        created_at=now,
                    )
                )

        for category_slug, category_data in kit_entries:
            category = kit_categories[category_slug]
            for item_sort_order, kit_item in enumerate(category_data["items"], start=1):
                item = ActionKitItem(
                    domain="kits",
                    category_id=category.id,
                    name=kit_item["name"],
                    summary=kit_item["summary"],
                    tag=kit_item.get("tag"),
                    file_type=kit_item.get("type") or "PDF",
                    dday=kit_item.get("dday"),
                    sort_order=item_sort_order,
                    is_active=True,
                    created_at=now,
                    updated_at=now,
                )
                session.add(item)
                await session.flush()

                for r_idx, related in enumerate(
                    kit_item.get("relatedLaws", []), start=1
                ):
                    if isinstance(related, str):
                        law_name = related
                        law_summary = None
                    else:
                        law_name = related.get("name", "")
                        law_summary = related.get("summary")
                    session.add(
                        ActionKitRelatedLaw(
                            item_id=item.id,
                            law_name=law_name,
                            law_summary=law_summary,
                            sort_order=r_idx,
                            created_at=now,
                        )
                    )

                source_path = _resolve_legacy_source(
                    backend_root=backend_root,
                    original_path=kit_item.get("path", ""),
                )
                filename = (
                    Path(_strip_prefix(kit_item.get("path", ""))).name
                    or f"kit-{item.id}.pdf"
                )
                object_key = _to_object_key(
                    domain="kits",
                    category_slug=category_slug,
                    item_id=item.id,
                    filename=filename,
                )
                target_path = storage_root / object_key
                target_path.parent.mkdir(parents=True, exist_ok=True)
                if source_path and source_path.exists() and not target_path.exists():
                    shutil.copy2(source_path, target_path)
                size_bytes = (
                    target_path.stat().st_size if target_path.exists() else None
                )
                checksum = file_checksum(target_path) if target_path.exists() else None
                mime_type = detect_mime_type(filename)

                session.add(
                    ActionKitFile(
                        item_id=item.id,
                        version=1,
                        object_key=object_key,
                        original_filename=filename,
                        mime_type=mime_type,
                        size_bytes=size_bytes,
                        checksum=checksum,
                        is_current=True,
                        uploaded_at=now,
                        created_at=now,
                    )
                )

        await session.commit()
        print("[seed_actionkit] seeded categories/items/files successfully.")


if __name__ == "__main__":
    asyncio.run(seed())
