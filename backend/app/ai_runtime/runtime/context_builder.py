from app.ai_runtime.modes import ModeSpec
from app.ai_runtime.schemas.chat import ChatRequest
from app.ai_runtime.schemas.tool import ToolResult


def _extract_hits(tool_results: list[ToolResult] | None) -> list[dict]:
    if not tool_results:
        return []

    hits: list[dict] = []
    for tool_result in tool_results:
        tool_hits = tool_result.output.get("hits", [])
        if isinstance(tool_hits, list):
            hits.extend(hit for hit in tool_hits if isinstance(hit, dict))
    return hits


def _extract_file_overviews(tool_results: list[ToolResult] | None) -> list[dict]:
    if not tool_results:
        return []

    overviews: list[dict] = []
    for tool_result in tool_results:
        if tool_result.name != "session_file_search":
            continue
        file_overviews = tool_result.output.get("file_overviews", [])
        if isinstance(file_overviews, list):
            overviews.extend(item for item in file_overviews if isinstance(item, dict))
    return overviews


def _format_file_locator(hit: dict) -> str | None:
    parts: list[str] = []
    if hit.get("page_number"):
        parts.append(f"p.{hit['page_number']}")
    if hit.get("sheet_name"):
        parts.append(f"sheet {hit['sheet_name']}")
    if hit.get("slide_number"):
        parts.append(f"slide {hit['slide_number']}")
    if hit.get("section_title"):
        parts.append(str(hit["section_title"]))
    return " / ".join(parts) or None


def _extract_report_carbon_outputs(tool_results: list[ToolResult] | None) -> list[dict]:
    if not tool_results:
        return []
    outputs: list[dict] = []
    for tool_result in tool_results:
        if tool_result.name != "report_carbon_extract_calc":
            continue
        if isinstance(tool_result.output, dict):
            outputs.append(tool_result.output)
    return outputs


def _format_file_overview_locator(chunk: dict) -> str:
    parts: list[str] = []
    if chunk.get("page_number"):
        parts.append(f"p.{chunk['page_number']}")
    if chunk.get("sheet_name"):
        parts.append(f"sheet {chunk['sheet_name']}")
    if chunk.get("slide_number"):
        parts.append(f"slide {chunk['slide_number']}")
    if chunk.get("section_title"):
        parts.append(str(chunk["section_title"]))
    return " / ".join(parts) or "无"


def build_context_bundle(
    request: ChatRequest,
    mode: ModeSpec,
    *,
    tool_results: list[ToolResult] | None = None,
) -> dict:
    if mode.name == "ask":
        knowledge_scope_requested = request.payload.get("knowledge_scope_requested", "public")
        knowledge_scope_effective = request.payload.get("knowledge_scope_effective", "public")
        recent_messages = request.payload.get("recent_messages", request.payload.get("session_context", []))
        session_summary = request.payload.get("session_summary")
        memory_notes = request.payload.get("memory_notes", [])
        context_usage_estimate = request.payload.get("context_usage_estimate", 0)
        context_budget_estimate = request.payload.get("context_budget_estimate", 258_000)
        compacted_message_count = request.payload.get("compacted_message_count", 0)
        compaction_status = request.payload.get("compaction_status", "idle")
        summary_updated_at = request.payload.get("summary_updated_at")
        attached_knowledge_item_ids = request.payload.get("attached_knowledge_item_ids", [])
        attached_file_knowledge_item_ids = request.payload.get("attached_file_knowledge_item_ids", [])
        kb_id = request.payload.get("kb_id")
        rag_mode = request.payload.get("rag_mode", "hybrid_rerank")
        retrieval_hits = _extract_hits(tool_results)
        file_overviews = _extract_file_overviews(tool_results)
        report_carbon_outputs = _extract_report_carbon_outputs(tool_results)
        public_hits = [hit for hit in retrieval_hits if hit.get("source_type") == "public_policy"]
        demo_policy_hits = [hit for hit in retrieval_hits if hit.get("source_type") == "public_policy_demo"]
        private_hits = [
            hit for hit in retrieval_hits if hit.get("source_type") in {"private_sample", "private_upload"}
        ]

        limitations = [
            "不得伪造引用，也不得声称访问了未检索到的外部证据。",
            "private sample 当前只是脱敏演示样例，不代表真实客户审计结果。",
            "用户上传文件只有在当前 session 已挂接且解析索引完成时，才可作为私有依据参与回答；若已检索到上传文件片段，应直接基于片段回答。",
        ]

        if session_summary:
            summary_lines = [
                "以下是当前会话的自动摘要，请优先据此理解较早上下文：",
                session_summary,
            ]
        else:
            summary_lines = ["当前会话尚未生成自动摘要。"]

        if recent_messages:
            session_context_lines = ["最近单会话历史如下，请仅用于延续当前会话上下文："]
            for index, message in enumerate(recent_messages, start=1):
                if not isinstance(message, dict):
                    continue
                role = message.get("role", "unknown")
                content = message.get("content", "")
                session_context_lines.append(f"[history-{index}] {role}: {content}")
        else:
            session_context_lines = ["当前会话历史为空，这是本轮对话的起点。"]
        if attached_knowledge_item_ids:
            session_context_lines.append(
                "当前 session 已挂接知识条目："
                + ", ".join(str(item_id) for item_id in attached_knowledge_item_ids)
            )
        else:
            session_context_lines.append("当前 session 尚未挂接可检索知识条目。")
        if attached_file_knowledge_item_ids:
            session_context_lines.append(
                "本轮用户显式选择了已解析上传文件："
                + ", ".join(str(item_id) for item_id in attached_file_knowledge_item_ids)
            )
        if kb_id:
            session_context_lines.append(f"本轮 AskPage 选择的 RAG 知识库：{kb_id}，检索模式：{rag_mode}。")

        if memory_notes:
            memory_note_lines = ["以下是用户级长期记忆预留条目，只用于补充稳定偏好或长期上下文："]
            for index, note in enumerate(memory_notes, start=1):
                if not isinstance(note, dict):
                    continue
                memory_note_lines.extend(
                    [
                        f"[memory-{index}] 标题：{note.get('title', '未命名记忆')}",
                        f"内容：{note.get('content', '')}",
                    ]
                )
        else:
            memory_note_lines = ["当前没有启用的长期记忆条目。"]

        evidence_lines: list[str] = []
        if public_hits:
            evidence_lines.append("当前已检索到以下公共政策片段：")
            for index, hit in enumerate(public_hits, start=1):
                evidence_lines.extend(
                    [
                        f"[policy-{index}] 标题：{hit['title']}",
                        f"发布机构：{hit['source']}",
                        f"片段标识：{hit['chunk_id']}",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
        if demo_policy_hits:
            evidence_lines.append("当前已检索到以下内置演示样例片段（非官方政策依据）：")
            for index, hit in enumerate(demo_policy_hits, start=1):
                evidence_lines.extend(
                    [
                        f"[policy-demo-{index}] 标题：{hit['title']}",
                        f"来源：{hit['source']}（演示样例，不代表真实官方政策）",
                        f"片段标识：{hit['chunk_id']}",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
        if private_hits:
            evidence_lines.append("当前已检索到以下私有知识或上传文件片段：")
            for index, hit in enumerate(private_hits, start=1):
                file_locator = _format_file_locator(hit)
                evidence_lines.extend(
                    [
                        f"[private-{index}] 标题：{hit['title']}",
                        f"来源类型：{hit['source_type']}",
                        f"来源：{hit['source']}",
                        f"片段标识：{hit['chunk_id']}",
                        f"文件定位：{file_locator}" if file_locator else "文件定位：无",
                        f"片段内容：{hit['snippet']}",
                    ]
                )
            if any(hit.get("source_type") == "private_upload" for hit in private_hits):
                evidence_lines.append(
                    "注意：本轮已命中用户上传文件片段。请优先基于这些片段回答用户关于报告、附件或文档内容的问题；不要再声称无法读取该文件。"
                )
        if file_overviews:
            evidence_lines.append("当前显式选择的上传文件结构化摘录如下，用于覆盖报告文字、表格、数字和早期章节；回答附件问题时应优先综合这些摘录与检索命中片段：")
            for file_index, overview in enumerate(file_overviews, start=1):
                evidence_lines.extend(
                    [
                        f"[upload-file-{file_index}] 标题：{overview.get('title')}",
                        f"来源：{overview.get('source')}；片段总数：{overview.get('chunk_count')}；表格/结构化片段：{overview.get('table_like_chunk_count')}；含数字片段：{overview.get('numeric_chunk_count')}",
                    ]
                )
                carbon_memory = overview.get("carbon_activity_memory")
                if isinstance(carbon_memory, dict):
                    memory_items = carbon_memory.get("items") or []
                    if isinstance(memory_items, list) and memory_items:
                        evidence_lines.append(
                            f"[upload-file-{file_index}-carbon-memory] 已从该文件抽取到 {carbon_memory.get('activity_count')} 条碳排放活动/消耗量候选，以下为会话内结构化文件记忆："
                        )
                        for item_index, item in enumerate(memory_items, start=1):
                            if not isinstance(item, dict):
                                continue
                            locator = _format_file_overview_locator(item)
                            factor_note = item.get("requested_factor_id") or "待匹配"
                            evidence_lines.extend(
                                [
                                    f"[upload-file-{file_index}-carbon-{item_index}] 范围：{item.get('scope')}；活动：{item.get('activity_category')}/{item.get('activity_name')}",
                                    f"消耗量：{item.get('activity_value')} {item.get('activity_unit')}；匹配别名：{item.get('matched_alias')}；因子ID：{factor_note}",
                                    f"定位：{locator}；chunk：{item.get('chunk_id')}；置信度：{item.get('confidence')}",
                                    f"证据片段：{item.get('snippet')}",
                                ]
                            )
                    warnings = carbon_memory.get("warnings") or []
                    if isinstance(warnings, list) and warnings:
                        evidence_lines.append(
                            f"[upload-file-{file_index}-carbon-memory-warnings] "
                            + "；".join(str(item) for item in warnings[:3])
                        )
                chunks = overview.get("chunks") or []
                if isinstance(chunks, list):
                    for chunk_index, chunk in enumerate(chunks, start=1):
                        if not isinstance(chunk, dict):
                            continue
                        locator = _format_file_overview_locator(chunk)
                        evidence_lines.extend(
                            [
                                f"[upload-file-{file_index}-excerpt-{chunk_index}] 类型：{chunk.get('content_kind')}；定位：{locator}；chunk：{chunk.get('chunk_id')}",
                                f"摘录内容：{chunk.get('snippet')}",
                            ]
                        )
            evidence_lines.append(
                "约束：如果用户询问上传报告中的总量、占比、表格数据、能源消耗或碳排放类别，必须先检查上述结构化摘录和碳活动记忆；只有摘录、活动记忆和命中片段都缺失时，才说明材料不足。"
            )
        for carbon_output in report_carbon_outputs:
            extracted_activities = carbon_output.get("extracted_activities") or []
            calculation = carbon_output.get("calculation") or {}
            warnings = carbon_output.get("warnings") or []
            evidence_lines.append("当前已从上传报告抽取到以下碳活动数据并按 CarbonRag 本地碳因子库完成匹配/核算：")
            if extracted_activities:
                for index, item in enumerate(extracted_activities, start=1):
                    locator_parts = []
                    if item.get("page_number"):
                        locator_parts.append(f"p.{item['page_number']}")
                    if item.get("sheet_name"):
                        locator_parts.append(f"sheet {item['sheet_name']}")
                    if item.get("slide_number"):
                        locator_parts.append(f"slide {item['slide_number']}")
                    locator = " / ".join(locator_parts) or "无"
                    evidence_lines.extend(
                        [
                            f"[report-carbon-{index}] 活动：{item.get('activity_category')}/{item.get('activity_name')}",
                            f"活动量：{item.get('activity_value')} {item.get('activity_unit')}",
                            f"本地因子匹配：{item.get('requested_factor_id') or item.get('metadata', {}).get('matched_factor_id') or '未指定'}；匹配方式：{item.get('metadata', {}).get('match_method') or '规则抽取'}",
                            f"证据文件：{item.get('title')}；定位：{locator}；chunk：{item.get('chunk_id')}",
                            f"证据片段：{item.get('snippet')}",
                        ]
                    )
            else:
                evidence_lines.append("未识别到受支持的活动量。")
            if calculation:
                evidence_lines.extend(
                    [
                        f"报告碳核算总量：{calculation.get('total_emission_kgco2e')} kgCO2e",
                        f"核算 trace_id：{calculation.get('trace_id')}；inventory_id：{calculation.get('inventory_id')}",
                        "核算分项："
                    ]
                )
                for item in calculation.get("breakdown") or []:
                    evidence_lines.append(
                        f"- {item.get('activity_name')}: {item.get('activity_value')} {item.get('activity_unit')} × "
                        f"{item.get('factor_value')} {item.get('factor_unit')} = {item.get('emission_kgco2e')} kgCO2e；因子ID：{item.get('factor_id')}"
                    )
                evidence_lines.append("约束：回答报告碳核算问题时，只能使用上述本地因子匹配与上传报告证据；不允许临时改用网络检索到的外部因子。")
            if warnings:
                evidence_lines.append("报告抽取/核算警告：" + "；".join(str(item) for item in warnings))
        if not evidence_lines:
            evidence_lines = [
                "当前未检索到足够依据。",
                "不得伪造引用，只能明确说明当前 scope 下未命中足够证据，并给出受限说明。",
            ]

        response_style_lines = [
            "回答格式要求：不要使用 Markdown 的 # / ## / ### 标题；用加粗短语作为小节标题即可。",
            "复杂问题必须先给一句结论，再按“关键依据、分步分析、风险/限制、下一步建议”组织；不要把主次混在同一段。",
            "涉及分类、对比、清单、能源类型、碳因子、活动量或核算结果时，优先使用 Markdown 表格；表格后再补充必要解释。",
            "每段只承载一个要点，避免长段堆叠；没有依据的数据必须标注为未确认或需要补充材料。",
        ]

        if knowledge_scope_effective == "public":
            scope_strategy_lines = [
                "当前策略：检索本地公共政策样本；若本轮用户显式选择了已解析上传文件，也可以同时引用该文件片段。",
                "不得声称使用了未选中、未解析或未命中的企业样例/上传附件。",
            ]
        elif knowledge_scope_effective == "private_sample":
            scope_strategy_lines = [
                "当前策略：仅检索当前 session 已关联的脱敏企业知识条目。",
                "必须明确这些样例仅用于演示，不代表真实企业审计结果。",
            ]
        else:
            scope_strategy_lines = [
                "当前策略：同时参考公共政策依据和当前 session 已关联的脱敏企业知识条目。",
                "回答时必须区分政策要求与样例现状，不能把企业知识条目当成政策依据。",
            ]

        return {
            "system_role": "CarbonRag 是一个面向中小企业的双碳问答 MVP。",
            "mode_name": "ask",
            "system_prompt": "\n".join(
                [
                    "你是 CarbonRag 的 ask mode 问答助手。",
                    "当前产品定位：面向中小企业的双碳问答 MVP。",
                    *summary_lines,
                    *session_context_lines,
                    *memory_note_lines,
                    *scope_strategy_lines,
                    "当前限制：只能基于会话上下文与已检索依据回答，不得伪造引用或未命中的数据。",
                    f"当前知识范围请求：{knowledge_scope_requested}。",
                    f"当前知识范围实际生效：{knowledge_scope_effective}。",
                    f"当前上下文占用估算：{context_usage_estimate} / {context_budget_estimate}。",
                    f"当前压缩状态：{compaction_status}，已摘要覆盖 {compacted_message_count} 条较早消息。",
                    *response_style_lines,
                    *evidence_lines,
                    "如果存在政策和样例两类依据，请分层表达“政策要求”与“样例现状”；如果片段不足，只能给出受限说明。",
                ]
            ),
            "user_question": request.user_input,
            "knowledge_scope_requested": knowledge_scope_requested,
            "knowledge_scope_effective": knowledge_scope_effective,
            "recent_messages": recent_messages,
            "session_summary": session_summary,
            "memory_notes": memory_notes,
            "policy_context": {
                "ready": True,
                "source": "local_public_policy_corpus",
                "hit_count": len(public_hits),
                "hits": public_hits,
            },
            "policy_demo_context": {
                "ready": bool(demo_policy_hits),
                "source": "built_in_showcase_fixture",
                "hit_count": len(demo_policy_hits),
                "hits": demo_policy_hits,
            },
            "enterprise_context": {
                "ready": True,
                "source": "local_private_sample_corpus",
                "hit_count": len(private_hits),
                "hits": private_hits,
                "file_overview_count": len(file_overviews),
                "file_overviews": file_overviews,
            },
            "report_carbon_context": {
                "ready": bool(report_carbon_outputs),
                "outputs": report_carbon_outputs,
            },
            "limitations": limitations,
            "session_state": {
                "trace_id": request.trace_id,
                "mode": mode.name,
                "attached_knowledge_item_ids": attached_knowledge_item_ids,
                "attached_file_knowledge_item_ids": attached_file_knowledge_item_ids,
                "kb_id": kb_id,
                "rag_mode": rag_mode,
                "compaction_status": compaction_status,
                "context_usage_estimate": context_usage_estimate,
                "context_budget_estimate": context_budget_estimate,
                "compacted_message_count": compacted_message_count,
                "summary_updated_at": summary_updated_at,
            },
            "memory_slot": {
                "status": "implemented",
                "implemented": True,
            },
            "payload_keys": sorted(request.payload.keys()),
        }

    return {
        "policy_context": {
            "ready": mode.name in {"ask", "report"},
            "source": "policy_stub",
        },
        "enterprise_context": {
            "ready": mode.name in {"ask", "carbon", "report"},
            "source": "enterprise_stub",
        },
        "carbon_context": {
            "ready": mode.name == "carbon",
            "source": "carbon_stub",
        },
        "report_context": {
            "ready": mode.name == "report",
            "source": "report_stub",
        },
        "session_state": {
            "trace_id": request.trace_id,
            "mode": mode.name,
        },
        "memory_slot": {
            "status": "reserved",
            "implemented": False,
        },
        "payload_keys": sorted(request.payload.keys()),
    }
