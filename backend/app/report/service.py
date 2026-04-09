from datetime import datetime, timezone
from uuid import uuid4

from app.ai_runtime.providers.base import ChatProviderError
from app.ai_runtime.providers.factory import get_chat_provider
from app.carbon.schemas import StoredCarbonCalculation
from app.carbon.service import CarbonService, get_carbon_service
from app.report.composer import ReportComposer
from app.report.renderer import ReportRenderError, parse_report_generation_payload, render_markdown_report
from app.report.schemas import (
    CreateReportRequest,
    ReportDetail,
    ReportSourceEntry,
    ReportSummary,
    StoredReport,
    UpdateReportRequest,
)
from app.report.storage import ReportStorage
from app.report.templates import get_report_template
from app.session.schemas import SessionDetail, SessionMessage
from app.session.service import SessionService, get_session_service


class ReportValidationError(ValueError):
    pass


class ReportProviderFailure(RuntimeError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class ReportService:
    def __init__(
        self,
        *,
        session_service: SessionService | None = None,
        carbon_service: CarbonService | None = None,
        storage: ReportStorage | None = None,
        composer: ReportComposer | None = None,
    ) -> None:
        self.session_service = session_service or get_session_service()
        self.carbon_service = carbon_service or get_carbon_service()
        self.storage = storage or ReportStorage()
        self.composer = composer or ReportComposer()

    def create_report(self, *, owner_user_id: str, payload: CreateReportRequest | dict) -> ReportDetail:
        payload = (
            payload
            if isinstance(payload, CreateReportRequest)
            else CreateReportRequest.model_validate(payload)
        )
        session = self.session_service.get_session(owner_user_id=owner_user_id, session_id=payload.session_id)
        if session is None:
            raise KeyError(payload.session_id)

        selected_messages = self._resolve_selected_messages(session, payload.source_message_ids)
        carbon_result = self._resolve_carbon_result(
            owner_user_id=owner_user_id,
            session_id=payload.session_id,
            carbon_result_id=payload.carbon_result_id,
        )
        self._validate_sources(
            report_type=payload.report_type,
            selected_messages=selected_messages,
            carbon_result=carbon_result,
        )

        template = get_report_template(payload.report_type)
        title = payload.title or self.composer.build_default_title(payload.report_type, session.title)
        message_citations = self.composer.collect_message_citations(selected_messages)
        carbon_citations = self.composer.collect_carbon_citations(carbon_result)
        citations = message_citations + carbon_citations
        source_summary = self.composer.build_source_summary(citations)

        provider_user_input = self.composer.build_provider_user_input(
            template=template,
            session=session,
            selected_messages=selected_messages,
            citations=citations,
            carbon_result=carbon_result,
            requested_title=title,
        )
        provider_system_prompt = self.composer.build_provider_system_prompt(template)

        try:
            provider_result = get_chat_provider().generate_response(
                system_prompt=provider_system_prompt,
                user_input=provider_user_input,
            )
            generation_payload = parse_report_generation_payload(provider_result.content, template)
        except (ChatProviderError, ReportRenderError) as exc:
            raise ReportProviderFailure(str(exc)) from exc

        timestamp = utcnow()
        report = StoredReport(
            report_id=f"report-{uuid4().hex[:12]}",
            session_id=payload.session_id,
            report_type=payload.report_type,
            title=generation_payload.title,
            content=render_markdown_report(
                title=generation_payload.title,
                sections=generation_payload.sections,
                references_markdown=self.composer.build_references_markdown(citations),
            ),
            output_format=payload.output_format,
            citations=citations,
            source_summary=source_summary,
            sources=self._build_sources(selected_messages, carbon_result),
            trace_id=f"report-trace-{uuid4().hex[:12]}",
            created_at=timestamp,
            updated_at=timestamp,
        )
        created = self.storage.create_report(owner_user_id=owner_user_id, report=report)
        self.session_service.record_system_message(
            owner_user_id=owner_user_id,
            session_id=payload.session_id,
            content=(
                f"已生成报告：{created.title}\n"
                f"报告类型：{created.report_type}\n"
                f"report_id：{created.report_id}"
            ),
        )
        return created

    def get_report(self, *, owner_user_id: str, report_id: str) -> ReportDetail | None:
        return self.storage.get_report(owner_user_id=owner_user_id, report_id=report_id)

    def update_report(self, *, owner_user_id: str, report_id: str, payload: UpdateReportRequest) -> ReportDetail | None:
        return self.storage.update_report(
            owner_user_id=owner_user_id,
            report_id=report_id,
            title=payload.title,
            content=payload.content,
            updated_at=utcnow(),
        )

    def list_session_reports(self, *, owner_user_id: str, session_id: str) -> list[ReportSummary]:
        self.session_service.require_session(owner_user_id=owner_user_id, session_id=session_id)
        return self.storage.list_session_reports(owner_user_id=owner_user_id, session_id=session_id)

    def list_session_carbon_results(self, *, owner_user_id: str, session_id: str):
        self.session_service.require_session(owner_user_id=owner_user_id, session_id=session_id)
        return self.carbon_service.list_session_calculations(owner_user_id=owner_user_id, session_id=session_id)

    @staticmethod
    def _resolve_selected_messages(session: SessionDetail, source_message_ids: list[str]) -> list[SessionMessage]:
        if not source_message_ids:
            return []

        message_map = {message.message_id: message for message in session.messages}
        selected_messages: list[SessionMessage] = []
        for message_id in source_message_ids:
            message = message_map.get(message_id)
            if message is None:
                raise ReportValidationError(f"Unknown message source: {message_id}")
            if message.role != "assistant":
                raise ReportValidationError("Only assistant messages can be selected as report sources.")
            selected_messages.append(message)
        return selected_messages

    def _resolve_carbon_result(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        carbon_result_id: str | None,
    ) -> StoredCarbonCalculation | None:
        if not carbon_result_id:
            return None

        stored = self.carbon_service.get_stored_calculation(owner_user_id=owner_user_id, trace_id=carbon_result_id)
        if stored is None:
            raise ReportValidationError(f"Unknown carbon result: {carbon_result_id}")
        if stored.session_id != session_id:
            raise ReportValidationError("Selected carbon result does not belong to the current session.")
        return stored

    @staticmethod
    def _validate_sources(
        *,
        report_type: str,
        selected_messages: list[SessionMessage],
        carbon_result: StoredCarbonCalculation | None,
    ) -> None:
        if report_type == "policy_summary":
            if not selected_messages:
                raise ReportValidationError("policy_summary requires at least one assistant message.")
            if not any(
                citation.source_type == "public_policy"
                for message in selected_messages
                for citation in message.citations
            ):
                raise ReportValidationError("policy_summary requires public policy citations.")
            return

        if report_type == "mixed_analysis":
            if not selected_messages:
                raise ReportValidationError("mixed_analysis requires at least one assistant message.")
            has_public = any(
                citation.source_type == "public_policy"
                for message in selected_messages
                for citation in message.citations
            )
            has_private = any(
                citation.source_type == "private_sample"
                for message in selected_messages
                for citation in message.citations
            )
            if not has_public or not has_private:
                raise ReportValidationError("mixed_analysis requires both public and private citations.")
            return

        if report_type == "carbon_summary":
            if carbon_result is None:
                raise ReportValidationError("carbon_summary requires a carbon_result_id.")
            return

        raise ReportValidationError(f"Unsupported report type: {report_type}")

    @staticmethod
    def _build_sources(
        selected_messages: list[SessionMessage],
        carbon_result: StoredCarbonCalculation | None,
    ) -> list[ReportSourceEntry]:
        sources: list[ReportSourceEntry] = []
        order_index = 0

        for message in selected_messages:
            sources.append(
                ReportSourceEntry(
                    source_type="message",
                    source_ref=message.message_id,
                    label=message.content[:40].strip() or message.message_id,
                    order_index=order_index,
                )
            )
            order_index += 1
            for citation in message.citations:
                sources.append(
                    ReportSourceEntry(
                        source_type="citation",
                        source_ref=f"{citation.source_type}:{citation.doc_id}:{citation.chunk_id}",
                        label=citation.title,
                        order_index=order_index,
                    )
                )
                order_index += 1

        if carbon_result is not None:
            sources.append(
                ReportSourceEntry(
                    source_type="carbon_result",
                    source_ref=carbon_result.trace_id,
                    label=carbon_result.period_label or carbon_result.trace_id,
                    order_index=order_index,
                )
            )

        return sources


def get_report_service() -> ReportService:
    return ReportService()
