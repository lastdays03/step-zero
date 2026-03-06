import os
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, HTTPException, Path, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_platform_admin
from app.api.v1.actionkit.schemas import ActionKitFileUploadResponse
from app.core.config import get_settings
from app.core.db import get_session
from app.features.actionkit.application import ActionKitService
from app.models.user import AuthenticatedUser
from app.repositories.actionkit_repository import ActionKitRepository
from app.repositories.file_repository import FileRepository
from app.services.storage import get_storage_backend

router = APIRouter()

VIEWABLE_EXTENSIONS = frozenset(
    {".md", ".markdown", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}
)


def _service(session: AsyncSession) -> ActionKitService:
    return ActionKitService(ActionKitRepository(session))


@router.post(
    "/items/{item_id}/files",
    response_model=ActionKitFileUploadResponse,
    summary="액션키트 파일 업로드",
    description="운영자가 액션키트 아이템에 파일을 업로드합니다.",
    response_description="업로드된 파일의 메타데이터를 반환합니다.",
)
async def upload_actionkit_file(
    item_id: int = Path(..., description="파일을 업로드할 액션키트 아이템 ID"),
    upload: UploadFile = File(..., description="업로드할 원본 파일"),
    _: AuthenticatedUser = Depends(require_platform_admin),
    session: AsyncSession = Depends(get_session),
):
    if not upload.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    try:
        payload = await _service(session).upload_item_file(
            item_id=item_id,
            upload_file=upload,
        )
        return ActionKitFileUploadResponse(**payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get(
    "/items/{item_id}",
    summary="액션키트 아이템 파일 뷰어 리다이렉트",
    description="아이템의 최신 파일 뷰어 URL로 리다이렉트합니다.",
    response_class=RedirectResponse,
    status_code=307,
)
async def redirect_item_to_view(
    item_id: int = Path(description="아이템 ID"),
):
    return f"/api/v1/actionkits/items/{item_id}/view"


_MD_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  body {{ max-width: 800px; margin: 2rem auto; padding: 0 1.5rem; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; color: #1e293b; line-height: 1.7; }}
  .doc-toolbar {{ position: sticky; top: 0; z-index: 10; display: flex; align-items: center; justify-content: space-between; padding: .75rem 1rem; margin: 0 -1.5rem 1.5rem; background: #fff; border-bottom: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,.05); }}
  .doc-toolbar h1 {{ font-size: 1rem; font-weight: 700; color: #1e293b; margin: 0; border: none; padding: 0; }}
  .doc-toolbar .btn-group {{ display: flex; gap: .5rem; }}
  .doc-toolbar .btn {{ display: inline-flex; align-items: center; gap: .35rem; padding: .4rem .85rem; border-radius: 6px; font-size: .8rem; font-weight: 600; text-decoration: none; border: 1px solid #e2e8f0; background: #fff; color: #475569; cursor: pointer; transition: background .15s; }}
  .doc-toolbar .btn:hover {{ background: #f1f5f9; }}
  .doc-toolbar .btn-primary {{ background: #36a4f2; color: #fff; border-color: #36a4f2; }}
  .doc-toolbar .btn-primary:hover {{ background: #258bd1; }}
  @media print {{ .doc-toolbar {{ display: none; }} }}
  h1 {{ border-bottom: 2px solid #e2e8f0; padding-bottom: .5rem; }}
  h2 {{ border-bottom: 1px solid #e2e8f0; padding-bottom: .3rem; margin-top: 2rem; }}
  h3 {{ margin-top: 1.5rem; }}
  pre {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 1rem; overflow-x: auto; }}
  code {{ background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-size: .9em; }}
  pre code {{ background: none; padding: 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
  th, td {{ border: 1px solid #e2e8f0; padding: .5rem .75rem; text-align: left; }}
  th {{ background: #f8fafc; font-weight: 600; }}
  blockquote {{ border-left: 4px solid #36a4f2; margin: 1rem 0; padding: .5rem 1rem; background: #f0f9ff; }}
  a {{ color: #36a4f2; }}
</style>
</head>
<body>
<div class="doc-toolbar">
  <h1>{title}</h1>
  <div class="btn-group">
    <a class="btn btn-primary" href="/api/v1/actionkits/items/{item_id}/download">원본 다운로드</a>
    <button class="btn" onclick="window.print()">인쇄 / PDF 저장</button>
  </div>
</div>
<div id="content"></div>
<script>
document.getElementById('content').innerHTML = marked.parse({markdown_json});
</script>
</body>
</html>"""


async def _resolve_file(item_id: int, session: AsyncSession):
    """Resolve item_id to (storage_key, current_file) or raise 404."""
    file_repo = FileRepository(session)
    files = await file_repo.get_current_files(
        owner_type="actionkit_item", owner_ids=[item_id]
    )
    if not files:
        raise HTTPException(status_code=404, detail="No file found for this item")

    current_file = files[0]
    storage_key = f"actionkit/{current_file.object_key}"
    return storage_key, current_file


@router.get(
    "/items/{item_id}/view",
    summary="액션키트 아이템 파일 뷰어",
    description="해당 아이템의 최신 파일을 브라우저에서 볼 수 있도록 제공합니다. "
    "Markdown 파일은 HTML로 변환, PDF는 인라인으로 표시합니다.",
)
async def view_item_current_file(
    item_id: int = Path(description="아이템 ID"),
    session: AsyncSession = Depends(get_session),
):
    storage_key, current_file = await _resolve_file(item_id, session)
    storage = get_storage_backend()
    settings = get_settings()
    filename = current_file.original_filename or "file"
    ext = os.path.splitext(filename)[1].lower()

    # Unsupported formats (HWP, PPTX, DOCX, ...) → redirect to download
    if ext not in VIEWABLE_EXTENSIONS:
        return RedirectResponse(
            url=f"/api/v1/actionkits/items/{item_id}/download",
            status_code=302,
        )

    # R2 mode: PDF/images → redirect to public URL
    if settings.STORAGE_BACKEND == "r2" and ext == ".pdf":
        return RedirectResponse(
            storage.get_public_url(storage_key), status_code=307
        )

    # Fetch file content (works for both local and R2)
    try:
        content = await storage.get(storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    # Markdown → HTML viewer (rendered client-side via marked.js)
    if ext in (".md", ".markdown"):
        import json as _json

        md_content = content.decode("utf-8")
        title = os.path.splitext(filename)[0]
        html = _MD_HTML_TEMPLATE.format(
            title=title,
            markdown_json=_json.dumps(md_content),
            item_id=item_id,
        )
        return HTMLResponse(content=html)

    # PDF, images → inline (browser renders natively)
    mime = current_file.mime_type or "application/octet-stream"
    if ext == ".pdf":
        mime = "application/pdf"

    encoded_filename = quote(filename)
    return Response(
        content=content,
        media_type=mime,
        headers={
            "Content-Disposition": f"inline; filename*=UTF-8''{encoded_filename}",
        },
    )


@router.get(
    "/items/{item_id}/download",
    summary="액션키트 아이템 최신 파일 다운로드",
    description="해당 아이템의 최신 버전 파일을 다운로드합니다.",
)
async def download_item_current_file(
    item_id: int = Path(description="다운로드할 아이템 ID"),
    session: AsyncSession = Depends(get_session),
):
    storage_key, current_file = await _resolve_file(item_id, session)
    storage = get_storage_backend()
    settings = get_settings()

    # R2 mode: redirect to public URL
    if settings.STORAGE_BACKEND == "r2":
        return RedirectResponse(
            storage.get_public_url(storage_key), status_code=307
        )

    # Local mode: serve file directly
    from app.services.storage.local import LocalStorageBackend

    if isinstance(storage, LocalStorageBackend):
        local_path = storage.get_local_path(storage_key)
        if not local_path.exists():
            raise HTTPException(status_code=404, detail="File not found on disk")
        return FileResponse(
            path=str(local_path),
            filename=current_file.original_filename or "download",
            media_type=current_file.mime_type or "application/octet-stream",
        )

    # Fallback: read bytes and return
    try:
        content = await storage.get(storage_key)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")

    return Response(
        content=content,
        media_type=current_file.mime_type or "application/octet-stream",
        headers={
            "Content-Disposition": f'attachment; filename*=UTF-8\'\'{quote(current_file.original_filename or "download")}',
        },
    )
