from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.file_preview import FilePreviewResponse, FilePreviewSourceType, get_file_preview_service

router = APIRouter(prefix="/file-previews")


def _safe_inline_media_type(mime_type: str) -> str:
    if mime_type in {"text/html", "application/xhtml+xml"}:
        return "text/plain; charset=utf-8"
    return mime_type


@router.get("/{source_type}/{source_id}", response_model=FilePreviewResponse)
def get_file_preview(
    source_type: FilePreviewSourceType,
    source_id: str,
    kb_id: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FilePreviewResponse:
    try:
        return get_file_preview_service().preview(
            source_type=source_type,
            source_id=source_id,
            kb_id=kb_id,
            current_user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="File preview is not allowed.") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "File preview source not found.") from exc


@router.get("/{source_type}/{source_id}/raw")
def get_file_preview_raw(
    source_type: FilePreviewSourceType,
    source_id: str,
    kb_id: str | None = Query(default=None),
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FileResponse:
    try:
        raw = get_file_preview_service().raw(
            source_type=source_type,
            source_id=source_id,
            kb_id=kb_id,
            current_user=current_user,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail="File preview is not allowed.") from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "File preview source not found.") from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"Raw file not found: {exc}") from exc
    return FileResponse(
        raw.path,
        media_type=_safe_inline_media_type(raw.mime_type),
        filename=raw.filename,
        content_disposition_type="inline",
    )
