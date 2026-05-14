from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.report.export.schemas import CreateReportExportRequest, ReportExportResponse
from app.report.export.service import ReportExportError, get_report_export_service

router = APIRouter()


@router.post("/reports/{report_id}/exports", response_model=ReportExportResponse)
def create_report_exports(
    report_id: str,
    payload: CreateReportExportRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportExportResponse:
    try:
        return get_report_export_service().create_exports(
            owner_user_id=current_user.user_id,
            report_id=report_id,
            payload=payload,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Report not found.")
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ReportExportError as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/reports/{report_id}/exports", response_model=ReportExportResponse)
def list_report_exports(
    report_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportExportResponse:
    try:
        return get_report_export_service().list_exports(owner_user_id=current_user.user_id, report_id=report_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Report not found.")


@router.get("/report-files/{file_id}/download")
def download_report_file(
    file_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> FileResponse:
    record = get_report_export_service().get_download_file(owner_user_id=current_user.user_id, file_id=file_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Report file not found.")
    return FileResponse(
        path=Path(record.storage_path),
        media_type=record.content_type,
        filename=record.filename,
    )
