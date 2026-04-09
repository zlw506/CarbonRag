from fastapi import APIRouter, HTTPException

from app.carbon.schemas import CarbonCalculationSummary
from app.report.schemas import CreateReportRequest, ReportDetail, ReportSummary, UpdateReportRequest
from app.report.service import ReportProviderFailure, ReportValidationError, get_report_service

router = APIRouter()


@router.post("/reports", response_model=ReportDetail)
def create_report(payload: CreateReportRequest) -> ReportDetail:
    try:
        return get_report_service().create_report(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
    except ReportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except ReportProviderFailure as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Report generation failed: {exc}")


@router.post("/generate-report", response_model=ReportDetail, deprecated=True)
def generate_report_alias(payload: CreateReportRequest) -> ReportDetail:
    return create_report(payload)


@router.get("/reports/{report_id}", response_model=ReportDetail)
def get_report(report_id: str) -> ReportDetail:
    report = get_report_service().get_report(report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在。")
    return report


@router.patch("/reports/{report_id}", response_model=ReportDetail)
def update_report(report_id: str, payload: UpdateReportRequest) -> ReportDetail:
    try:
        report = get_report_service().update_report(report_id, payload)
    except ReportValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if report is None:
        raise HTTPException(status_code=404, detail="报告不存在。")
    return report


@router.get("/sessions/{session_id}/reports", response_model=list[ReportSummary])
def list_session_reports(session_id: str) -> list[ReportSummary]:
    try:
        return get_report_service().list_session_reports(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")


@router.get("/sessions/{session_id}/carbon-calculations", response_model=list[CarbonCalculationSummary])
def list_session_carbon_results(session_id: str) -> list[CarbonCalculationSummary]:
    try:
        return get_report_service().list_session_carbon_results(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="会话不存在。")
