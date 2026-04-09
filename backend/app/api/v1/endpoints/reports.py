from fastapi import APIRouter, Depends, HTTPException

from app.auth.dependencies import require_authenticated_user
from app.auth.schemas import AuthenticatedUser
from app.carbon.schemas import CarbonCalculationSummary
from app.report.schemas import CreateReportRequest, ReportDetail, ReportSummary, UpdateReportRequest
from app.report.service import ReportProviderFailure, ReportValidationError, get_report_service

router = APIRouter()


@router.post("/reports", response_model=ReportDetail)
def create_report(
    payload: CreateReportRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportDetail:
    try:
        return get_report_service().create_report(owner_user_id=current_user.user_id, payload=payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
    except ReportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ReportProviderFailure as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")


@router.post("/generate-report", response_model=ReportDetail, deprecated=True)
def generate_report_alias(
    payload: CreateReportRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportDetail:
    return create_report(payload=payload, current_user=current_user)


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(
    report_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportDetail:
    report = get_report_service().get_report(owner_user_id=current_user.user_id, report_id=report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.patch("/reports/{report_id}", response_model=ReportDetail)
def update_report(
    report_id: str,
    payload: UpdateReportRequest,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> ReportDetail:
    try:
        report = get_report_service().update_report(
            owner_user_id=current_user.user_id,
            report_id=report_id,
            payload=payload,
        )
    except ReportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/sessions/{session_id}/reports", response_model=list[ReportSummary])
def list_session_reports(
    session_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[ReportSummary]:
    try:
        return get_report_service().list_session_reports(owner_user_id=current_user.user_id, session_id=session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")


@router.get("/sessions/{session_id}/carbon-calculations", response_model=list[CarbonCalculationSummary])
def list_session_carbon_results(
    session_id: str,
    current_user: AuthenticatedUser = Depends(require_authenticated_user),
) -> list[CarbonCalculationSummary]:
    try:
        return get_report_service().list_session_carbon_results(owner_user_id=current_user.user_id, session_id=session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found.")
