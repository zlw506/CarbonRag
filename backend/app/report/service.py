from datetime import datetime, timezone
from uuid import uuid4

from app.ai_runtime.providers.base import ChatProviderError
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
from app.settings.service import get_settings_service
from app.report.templates import get_report_template
from app.session.schemas import SessionDetail, SessionMessage
from app.session.service import SessionService, get_session_service


def get_chat_provider(*, owner_user_id: str | None = None, provider_override=None):
    if owner_user_id is None and provider_override is None:
        from app.ai_runtime.providers.factory import get_chat_provider as get_default_chat_provider

        return get_default_chat_provider()

    if owner_user_id is None:
        raise ReportValidationError("owner_user_id is required when resolving a custom provider.")

    _, chat_provider = get_settings_service().build_chat_provider(
        owner_user_id=owner_user_id,
        provider_override=provider_override,
    )
    return chat_provider


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

        selected_messages = self._resolve_selected_messages(
            session,
            payload.source_message_ids,
            report_type=payload.report_type,
        )
        carbon_result = self._resolve_carbon_result(
            owner_user_id=owner_user_id,
            session_id=payload.session_id,
            carbon_result_id=payload.carbon_result_id,
            report_type=payload.report_type,
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
            try:
                chat_provider = get_chat_provider(
                    owner_user_id=owner_user_id,
                    provider_override=payload.provider_override,
                )
            except TypeError:
                chat_provider = get_chat_provider()
            provider_result = chat_provider.generate_response(
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

    def create_conversation_draft_report(
        self,
        *,
        owner_user_id: str,
        session_id: str,
        report_type: str = "mixed_analysis",
        title: str | None = None,
        request_text: str | None = None,
        validation_warning: str | None = None,
    ) -> ReportDetail:
        """Create a downloadable report draft even when strict citation gates are not met.

        Chat-triggered file generation should produce an artifact immediately. The strict
        `create_report` path remains the formal, citation-controlled route; this method is
        an explicit draft fallback so the UI can return a DOCX/PDF link instead of only an
        explanation.
        """

        session = self.session_service.get_session(owner_user_id=owner_user_id, session_id=session_id)
        if session is None:
            raise KeyError(session_id)

        selected_messages = self._pick_draft_source_messages(session.messages)
        citations = self.composer.collect_message_citations(selected_messages)
        source_summary = self.composer.build_source_summary(citations)
        timestamp = utcnow()
        report_title = title or f"对话即时报告 - {session.title}"
        report = StoredReport(
            report_id=f"report-{uuid4().hex[:12]}",
            session_id=session_id,
            report_type=report_type,
            title=report_title,
            content=self._build_conversation_draft_markdown(
                title=report_title,
                session=session,
                request_text=request_text,
                selected_messages=selected_messages,
                citations=citations,
                validation_warning=validation_warning,
            ),
            output_format="markdown",
            citations=citations,
            source_summary=source_summary,
            sources=self._build_sources(selected_messages, None),
            trace_id=f"report-trace-draft-{uuid4().hex[:12]}",
            created_at=timestamp,
            updated_at=timestamp,
        )
        created = self.storage.create_report(owner_user_id=owner_user_id, report=report)
        self.session_service.record_system_message(
            owner_user_id=owner_user_id,
            session_id=session_id,
            content=(
                f"已生成即时报告草稿：{created.title}\n"
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
    def _resolve_selected_messages(
        session: SessionDetail,
        source_message_ids: list[str],
        *,
        report_type: str,
    ) -> list[SessionMessage]:
        if not source_message_ids:
            fallback = ReportService._pick_default_message(session.messages, report_type)
            return [fallback] if fallback is not None else []

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
        report_type: str,
    ) -> StoredCarbonCalculation | None:
        if not carbon_result_id:
            if report_type != "carbon_summary":
                return None
            recent_results = self.carbon_service.list_session_calculations(
                owner_user_id=owner_user_id,
                session_id=session_id,
            )
            if not recent_results:
                return None
            carbon_result_id = recent_results[0].trace_id

        stored = self.carbon_service.get_stored_calculation(owner_user_id=owner_user_id, trace_id=carbon_result_id)
        if stored is None:
            raise ReportValidationError(f"Unknown carbon result: {carbon_result_id}")
        if stored.session_id != session_id:
            raise ReportValidationError("Selected carbon result does not belong to the current session.")
        return stored

    @staticmethod
    def _is_private_citation(source_type: str) -> bool:
        return source_type in {"private_sample", "private_upload"}

    @staticmethod
    def _pick_default_message(messages: list[SessionMessage], report_type: str) -> SessionMessage | None:
        candidates = [
            message
            for message in reversed(messages)
            if message.role == "assistant" and message.citations
        ]
        if not candidates:
            return None

        if report_type == "mixed_analysis":
            return next(
                (
                    message
                    for message in candidates
                    if any(citation.source_type == "public_policy" for citation in message.citations)
                    and any(ReportService._is_private_citation(citation.source_type) for citation in message.citations)
                ),
                None,
            ) or candidates[0]

        if report_type == "policy_summary":
            return next(
                (
                    message
                    for message in candidates
                    if any(citation.source_type == "public_policy" for citation in message.citations)
                ),
                None,
            ) or candidates[0]

        return candidates[0]

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
                ReportService._is_private_citation(citation.source_type)
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

    @staticmethod
    def _pick_draft_source_messages(messages: list[SessionMessage]) -> list[SessionMessage]:
        useful_messages = [
            message
            for message in messages
            if message.role == "assistant"
            and message.content.strip()
            and message.status != "failed"
            and not _is_placeholder_message(message.content)
        ]
        return useful_messages[-6:]

    @staticmethod
    def _build_conversation_draft_markdown(
        *,
        title: str,
        session: SessionDetail,
        request_text: str | None,
        selected_messages: list[SessionMessage],
        citations: list,
        validation_warning: str | None,
    ) -> str:
        lines: list[str] = [
            f"# {title}",
            "",
            "> 本文件由聊天页即时生成，可先下载使用；若需要正式合规版，请补齐政策/知识库 citation 后重新导出。",
            "",
            "## 生成说明",
            f"- 会话：{session.title}",
            f"- 生成时间：{utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        ]
        if request_text:
            lines.append(f"- 用户指令：{_one_line(request_text, limit=180)}")
        if validation_warning:
            lines.append(f"- 正式报告校验未满足：{validation_warning}")
        lines.extend(
            [
                "",
                "## 报告正文",
            ]
        )

        if selected_messages:
            for index, message in enumerate(selected_messages, start=1):
                lines.extend(
                    [
                        f"### 会话要点 {index}",
                        _trim_block(message.content, limit=1600),
                        "",
                    ]
                )
        else:
            lines.extend(
                [
                    "当前会话还没有可用于正式整理的助手回复。请把需要整理的材料继续发到聊天中，或在生成正式报告前先完成一次带依据的问答。",
                    "",
                ]
            )

        lines.extend(
            [
                "## 后续补充建议",
                "- 若要生成正式政策报告，请先让问答命中公共政策 citation。",
                "- 若要生成企业资料分析报告，请先上传文件并确认回答中出现 private_upload citation。",
                "- 若要生成碳核算报告，请先完成碳核算结果并确认使用了碳因子依据。",
                "",
                "## 参考依据",
            ]
        )
        if citations:
            for citation in citations:
                lines.append(f"- [{citation.source_type}] {citation.title}：{citation.snippet}")
        else:
            lines.append("- 暂无正式 citation。本报告为即时草稿，不应作为最终可审计报告。")

        return "\n".join(lines).strip() + "\n"


def get_report_service() -> ReportService:
    return ReportService()


def _is_placeholder_message(content: str) -> bool:
    normalized = content.strip()
    return normalized in {
        "正在准备回答...",
        "正在为这条问题创建回答位...",
        "正在结合上下文组织回答...",
    }


def _one_line(content: str, *, limit: int) -> str:
    return _trim_block(" ".join(content.split()), limit=limit)


def _trim_block(content: str, *, limit: int) -> str:
    normalized = content.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}……"
