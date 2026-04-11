import {
    CompressOutlined,
    ExpandOutlined,
    FileTextOutlined,
    LinkOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    MessageOutlined,
    MoreOutlined,
    PaperClipOutlined,
    PlusOutlined,
    SettingOutlined,
    TagsOutlined,
} from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Checkbox,
    Collapse,
    Drawer,
    Empty,
    Input,
    List,
    Popover,
    Segmented,
    Space,
    Spin,
    Tag,
    Tooltip,
    Typography,
} from "antd";
import { useEffect, useMemo, useRef, useState } from "react";
import type { ChangeEvent, KeyboardEvent } from "react";
import ReactMarkdown from "react-markdown";
import { useSearchParams } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";
import { FeedbackButtonGroup } from "../../components/FeedbackButtonGroup";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { uploadSessionFile } from "../../services/files";
import { listAttachableKnowledgeItems, replaceAttachedKnowledgeItems } from "../../services/knowledge";
import {
    createSession,
    getSession,
    listSessions,
    submitSessionAskStreamRequest,
} from "../../services/sessions";
import type {
    AskCitation,
    AskResponse,
    AskSourceSummary,
    AskStatus,
    AskStreamDeltaEvent,
    AskStreamErrorEvent,
    AskStreamMetadataEvent,
    AskStreamMessageStartEvent,
    AskStreamStatusEvent,
    KnowledgeScope,
} from "../../types/ask";
import type { KnowledgeItem } from "../../types/knowledge";
import type { SessionAttachment, SessionDetail, SessionMessage, SessionSummary } from "../../types/session";

type AssistantLifecycleState = "pending" | "thinking" | "streaming" | "done" | "error";

interface ChatMessageView extends SessionMessage {
    client_state?: AssistantLifecycleState;
    thinking_content?: string;
}

interface ChatDraft {
    userMessage: ChatMessageView;
    assistantMessage: ChatMessageView;
}

interface StreamContextSource {
    recent_message_count: number;
    summary_present: boolean;
    citation_count: number;
}

export function AskPage() {
    const { user } = useAuth();
    const [searchParams, setSearchParams] = useSearchParams();
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const streamAbortRef = useRef<AbortController | null>(null);
    const messageStreamEndRef = useRef<HTMLDivElement | null>(null);
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [selectedCitationMessageId, setSelectedCitationMessageId] = useState<string | null>(null);
    const [streamDraft, setStreamDraft] = useState<ChatDraft | null>(null);
    const [streamMemoryState, setStreamMemoryState] = useState<SessionDetail["memory_state"] | null>(null);
    const [streamContextSource, setStreamContextSource] = useState<StreamContextSource | null>(null);
    const [question, setQuestion] = useState("");
    const [knowledgeScope, setKnowledgeScope] = useState<KnowledgeScope>("public");
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
    const [privateSampleDrawerOpen, setPrivateSampleDrawerOpen] = useState(false);
    const [draftAttachedDocIds, setDraftAttachedDocIds] = useState<string[]>([]);
    const [savingAttachedSamples, setSavingAttachedSamples] = useState(false);
    const [loadingPrivateSamples, setLoadingPrivateSamples] = useState(true);
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [loadingSessionDetail, setLoadingSessionDetail] = useState(false);
    const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
    const [sidePanelOpen, setSidePanelOpen] = useState(false);
    const [sending, setSending] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);
    const focusModeEnabled = searchParams.get("focus") !== "0";
    const isAdmin = user?.role === "admin";

    const visibleMessages = useMemo<ChatMessageView[]>(() => {
        const baseMessages = (activeSession?.messages ?? []) as ChatMessageView[];
        if (!streamDraft) {
            return baseMessages;
        }
        return [...baseMessages, streamDraft.userMessage, streamDraft.assistantMessage];
    }, [activeSession?.messages, streamDraft]);

    const selectedCitationMessage = visibleMessages.find((message) => message.message_id === selectedCitationMessageId) ?? null;
    const citationGroups = groupCitationsBySource(selectedCitationMessage?.citations ?? []);
    const uploadedAttachments = activeSession?.attached_files.filter((item) => item.source_type === "uploaded_file") ?? [];
    const privateAttachments = activeSession?.attached_files.filter((item) => item.source_type !== "uploaded_file") ?? [];
    const currentSourceSummary = buildPanelSourceSummary(selectedCitationMessage?.citations ?? [], activeSession?.source_summary);
    const effectiveMemoryState = streamMemoryState ?? activeSession?.memory_state ?? null;
    const currentStreamState = streamDraft?.assistantMessage.client_state ?? null;
    const currentStreamTag = currentStreamState ? lifecycleTagMap[currentStreamState] : null;
    const contextUsagePercent = getContextUsagePercent(effectiveMemoryState);
    const compactContextSummary = buildCompactContextSummary(effectiveMemoryState, currentSourceSummary, streamContextSource);
    const currentContextSourceText = buildContextSourceText(
        effectiveMemoryState,
        currentSourceSummary,
        visibleMessages.length,
        streamContextSource,
    );

    useEffect(() => {
        void bootstrapWorkbench();
    }, []);

    useEffect(() => {
        if (!activeSessionId) {
            return;
        }
        streamAbortRef.current?.abort();
        streamAbortRef.current = null;
        setStreamDraft(null);
        setStreamMemoryState(null);
        setStreamContextSource(null);
        void loadSessionDetail(activeSessionId);
    }, [activeSessionId]);

    useEffect(() => {
        return () => {
            streamAbortRef.current?.abort();
        };
    }, []);

    useEffect(() => {
        const node = messageStreamEndRef.current;
        if (!node) {
            return;
        }
        node.scrollIntoView({ behavior: "smooth", block: "end" });
    }, [visibleMessages, loadingSessionDetail, streamDraft]);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }

        const syncSidebarState = () => {
            setSidebarCollapsed((current) => {
                if (window.innerWidth <= 1200) {
                    return true;
                }
                if (window.innerWidth >= 1440) {
                    return current;
                }
                return current;
            });
        };

        syncSidebarState();
        window.addEventListener("resize", syncSidebarState);
        return () => window.removeEventListener("resize", syncSidebarState);
    }, []);

    async function bootstrapWorkbench() {
        setLoadingSessions(true);
        setLoadingPrivateSamples(true);
        setTransportError(null);

        try {
            const [sessionList, knowledgeCatalog] = await Promise.all([listSessions(), listAttachableKnowledgeItems()]);
            setKnowledgeItems(knowledgeCatalog);

            if (sessionList.length === 0) {
                const created = await createSession();
                setSessions([created]);
                setActiveSessionId(created.session_id);
                return;
            }

            setSessions(sessionList);
            setActiveSessionId((current) => current ?? sessionList[0].session_id);
        } catch {
            setTransportError("当前无法初始化对话工作台，请确认后端已启动。");
        } finally {
            setLoadingSessions(false);
            setLoadingPrivateSamples(false);
        }
    }

    async function refreshSessions(preferredSessionId?: string) {
        const sessionList = await listSessions();
        setSessions(sessionList);
        if (!sessionList.length) {
            return;
        }

        const targetId = preferredSessionId && sessionList.some((item) => item.session_id === preferredSessionId)
            ? preferredSessionId
            : sessionList[0].session_id;
        setActiveSessionId(targetId);
    }

    async function loadSessionDetail(sessionId: string) {
        setLoadingSessionDetail(true);
        setTransportError(null);

        try {
            const detail = await getSession(sessionId);
            setActiveSession(detail);
            setKnowledgeScope(detail.knowledge_scope_last_used ?? "public");
            setDraftAttachedDocIds(getAttachedPrivateSampleIds(detail.attached_files));
            setSelectedCitationMessageId(resolvePreferredCitationMessageId(detail));
        } catch {
            setActiveSession(null);
            setTransportError("当前无法读取选中会话，请稍后重试。");
        } finally {
            setLoadingSessionDetail(false);
        }
    }

    async function handleCreateSession() {
        setTransportError(null);
        try {
            const created = await createSession();
            setKnowledgeScope("public");
            await refreshSessions(created.session_id);
        } catch {
            setTransportError("当前无法创建新会话，请稍后重试。");
        }
    }

    async function handleSaveAttachedSamples() {
        if (!activeSessionId) {
            return;
        }
        setSavingAttachedSamples(true);
        setTransportError(null);
        try {
            const detail = await replaceAttachedKnowledgeItems(activeSessionId, draftAttachedDocIds);
            setActiveSession(detail);
            setDraftAttachedDocIds(getAttachedPrivateSampleIds(detail.attached_files));
            await refreshSessions(activeSessionId);
            setPrivateSampleDrawerOpen(false);
        } catch (error) {
            setTransportError(extractDetailMessage(error) ?? "当前无法保存知识条目挂接状态。");
        } finally {
            setSavingAttachedSamples(false);
        }
    }

    async function handleSubmit() {
        const trimmed = question.trim();
        if (!activeSessionId) {
            setTransportError("当前没有可用会话，请先创建会话。");
            return;
        }
        if (!trimmed) {
            setTransportError("问题不能为空。");
            return;
        }

        setSending(true);
        setTransportError(null);
        streamAbortRef.current?.abort();
        const controller = new AbortController();
        streamAbortRef.current = controller;
        setStreamMemoryState(null);
        setStreamContextSource(null);

        const draftUserMessageId = createDraftMessageId("user");
        const draftAssistantMessageId = createDraftMessageId("assistant");
        const now = new Date().toISOString();
        const draftQuestion = trimmed;
        setSelectedCitationMessageId(draftAssistantMessageId);

        setStreamDraft({
            userMessage: {
                message_id: draftUserMessageId,
                role: "user",
                content: draftQuestion,
                created_at: now,
                citations: [],
            },
            assistantMessage: {
                message_id: draftAssistantMessageId,
                role: "assistant",
                content: "",
                created_at: now,
                status: "pending",
                citations: [],
                client_state: "pending",
                thinking_content: "",
            },
        });
        setQuestion("");

        try {
            const response = await submitSessionAskStreamRequest(
                activeSessionId,
                {
                    question: draftQuestion,
                    knowledge_scope: knowledgeScope,
                    top_k: 5,
                    attached_file_ids: knowledgeScope === "public" ? [] : draftAttachedDocIds,
                },
                {
                onMessageStart: (event) => {
                    setSelectedCitationMessageId(event.assistant_message_id ?? draftAssistantMessageId);
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        userMessage: {
                            ...draft.userMessage,
                            message_id: event.user_message_id ?? draft.userMessage.message_id,
                        },
                        assistantMessage: {
                            ...draft.assistantMessage,
                            message_id: event.assistant_message_id ?? draft.assistantMessage.message_id,
                            trace_id: event.trace_id ?? draft.assistantMessage.trace_id ?? null,
                            status: "thinking",
                            client_state: "thinking",
                        },
                    })));
                },
                onStatus: (event) => {
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => {
                        const nextState = mapLifecycleStatusToMessageState(event.status);
                        return {
                            ...draft,
                            assistantMessage: {
                                ...draft.assistantMessage,
                                status: nextState.status,
                                client_state: nextState.client_state,
                            },
                        };
                    }));
                },
                onThinkingDelta: (event) => {
                    const delta = extractDeltaText(event);
                    if (!delta) {
                        return;
                    }
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        assistantMessage: {
                            ...draft.assistantMessage,
                            status: "thinking",
                            client_state: "thinking",
                            thinking_content: `${draft.assistantMessage.thinking_content ?? ""}${delta}`,
                        },
                    })));
                },
                onAnswerDelta: (event) => {
                    const delta = extractDeltaText(event);
                    if (!delta) {
                        return;
                    }
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        assistantMessage: {
                            ...draft.assistantMessage,
                            status: "streaming",
                            client_state: "streaming",
                            content: `${draft.assistantMessage.content}${delta}`,
                        },
                    })));
                },
                onMetadata: (event) => {
                    setSelectedCitationMessageId(event.assistant_message_id ?? draftAssistantMessageId);
                    setStreamMemoryState(normalizeAskStreamMemoryState(event.memory_state));
                    setStreamContextSource(event.context_source ?? null);
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        assistantMessage: mergeStreamMetadata(draft.assistantMessage, event),
                    })));
                },
                onDone: (event) => {
                    setSelectedCitationMessageId(event.assistant_message_id ?? draftAssistantMessageId);
                    setStreamMemoryState(normalizeAskStreamMemoryState(event.memory_state));
                    setStreamContextSource(event.context_source ?? null);
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        assistantMessage: {
                            ...mergeStreamMetadata(draft.assistantMessage, event),
                            status: event.status ?? "ok",
                            client_state: "done",
                        },
                    })));
                },
                onError: (event) => {
                    setSelectedCitationMessageId(event.assistant_message_id ?? draftAssistantMessageId);
                    setStreamDraft((current) => updateStreamDraft(current, (draft) => ({
                        ...draft,
                        assistantMessage: {
                            ...draft.assistantMessage,
                            status: event.status ?? "provider_error",
                            client_state: "error",
                            content: event.message ?? event.detail ?? "当前问答服务暂不可用，请稍后重试。",
                        },
                    })));
                },
                },
                { signal: controller.signal },
            );

            if (response.status === "invalid_input") {
                setTransportError(response.answer);
            }
            if (response.status === "provider_error") {
                setTransportError("模型服务当前响应失败，系统已把这次失败记录到当前会话。");
            }

            await refreshSessions(activeSessionId);
            await loadSessionDetail(activeSessionId);
        } catch (error) {
            if (controller.signal.aborted || isAbortLikeError(error)) {
                return;
            }
            if (isAskResponse(error)) {
                if (error.status === "invalid_input") {
                    setTransportError(error.answer);
                } else {
                    setTransportError("模型服务当前响应失败，系统已把这次失败记录到当前会话。");
                    await refreshSessions(activeSessionId);
                    await loadSessionDetail(activeSessionId);
                }
            } else {
                setTransportError("当前问答服务暂不可达，请确认后端已启动且模型服务可用。");
            }
        } finally {
            setSending(false);
            streamAbortRef.current = null;
            setStreamDraft(null);
        }
    }

    async function handleUploadChange(event: ChangeEvent<HTMLInputElement>) {
        const file = event.target.files?.[0];
        event.target.value = "";
        if (!file || !activeSessionId) {
            return;
        }

        setUploading(true);
        setUploadError(null);
        try {
            await uploadSessionFile(activeSessionId, file);
            await refreshSessions(activeSessionId);
            await loadSessionDetail(activeSessionId);
        } catch (error) {
            setUploadError(extractDetailMessage(error) ?? "附件上传失败，请确认文件格式、大小和会话状态。");
        } finally {
            setUploading(false);
        }
    }

    function openCitationPanel(messageId: string) {
        setSelectedCitationMessageId(messageId);
        setSidePanelOpen(true);
    }

    function toggleFocusMode() {
        const nextParams = new URLSearchParams(searchParams);
        if (focusModeEnabled) {
            nextParams.set("focus", "0");
        } else {
            nextParams.delete("focus");
        }
        setSearchParams(nextParams, { replace: true });
    }

    function handleComposerKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
        if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
            event.stopPropagation();
            return;
        }

        if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
            event.preventDefault();
            if (!sending) {
                void handleSubmit();
            }
        }
    }

    const contextDetailOverlay = (
        <div className="chat-context-popover">
            <Space size={8} wrap>
                {effectiveMemoryState ? (
                    <>
                        <Tag>
                            占用（估算）：{formatContextEstimate(effectiveMemoryState.context_usage_estimate)} / {formatContextEstimate(effectiveMemoryState.context_budget_estimate)}
                        </Tag>
                        <Tag>已摘要覆盖：{effectiveMemoryState.compacted_message_count} 条</Tag>
                        <Tag>摘要状态：{effectiveMemoryState.summary_present ? "已启用" : "未启用"}</Tag>
                        <Tag>
                            最近摘要：{effectiveMemoryState.summary_updated_at ? formatTimestamp(effectiveMemoryState.summary_updated_at) : "暂无"}
                        </Tag>
                    </>
                ) : (
                    <Tag>当前暂无会话摘要状态。</Tag>
                )}
            </Space>
            <Typography.Paragraph type="secondary" className="chat-context-popover__hint">
                {effectiveMemoryState ? buildMemoryHint(effectiveMemoryState) : currentContextSourceText}
            </Typography.Paragraph>
        </div>
    );

    const composerSettings = (
        <div className="chat-composer-settings">
            <Typography.Text strong>问答范围</Typography.Text>
            <Segmented<KnowledgeScope>
                value={knowledgeScope}
                onChange={(value) => setKnowledgeScope(value)}
                options={[
                    { label: "公共政策", value: "public" },
                    { label: "知识条目", value: "private_sample" },
                    { label: "混合", value: "mixed" },
                ]}
            />
            <Button icon={<TagsOutlined />} onClick={() => setPrivateSampleDrawerOpen(true)} disabled={loadingPrivateSamples}>
                管理知识条目挂接
            </Button>
            <Typography.Paragraph type="secondary" className="chat-composer-settings__hint">
                默认优先把输入框留在视觉中心。范围和知识条目挂接放到这里按需调整。
            </Typography.Paragraph>
        </div>
    );

    return (
        <div
            className={
                sidebarCollapsed
                    ? `chat-workbench${focusModeEnabled ? " chat-workbench--focus-mode" : ""} chat-workbench--sidebar-collapsed`
                    : `chat-workbench${focusModeEnabled ? " chat-workbench--focus-mode" : ""}`
            }
        >
            <div className="chat-workbench__sidebar">
                <Card
                    className="chat-sidebar-card"
                    title={sidebarCollapsed ? "会话" : "会话列表"}
                    extra={(
                        <Space size={8}>
                            <Tooltip title={sidebarCollapsed ? "展开会话栏" : "收起会话栏"}>
                                <Button
                                    icon={sidebarCollapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                                    onClick={() => setSidebarCollapsed((current) => !current)}
                                />
                            </Tooltip>
                            <Tooltip title="新建对话">
                                <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>
                                    {sidebarCollapsed ? "" : "新建对话"}
                                </Button>
                            </Tooltip>
                        </Space>
                    )}
                >
                    {!sidebarCollapsed ? (
                        <Typography.Paragraph type="secondary">
                            中间消息区是主视觉区；这里只保留会话切换。
                        </Typography.Paragraph>
                    ) : null}
                    {loadingSessions ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : (
                        <List
                            className={sidebarCollapsed ? "chat-session-list chat-session-list--collapsed" : "chat-session-list"}
                            dataSource={sessions}
                            locale={{ emptyText: "当前还没有会话。" }}
                            renderItem={(session) => (
                                <List.Item
                                    className={activeSessionId === session.session_id ? "chat-session-list__item chat-session-list__item--active" : "chat-session-list__item"}
                                    onClick={() => setActiveSessionId(session.session_id)}
                                >
                                    {sidebarCollapsed ? (
                                        <Tooltip title={`${session.title} · ${session.message_count} 条消息`}>
                                            <div className="chat-session-list__mini">
                                                <Typography.Text strong>{session.title.slice(0, 2)}</Typography.Text>
                                            </div>
                                        </Tooltip>
                                    ) : (
                                        <div className="chat-session-list__content">
                                            <Typography.Text strong>{session.title}</Typography.Text>
                                            <Typography.Text type="secondary" className="chat-session-list__meta">
                                                {buildSessionRailMeta(session)}
                                            </Typography.Text>
                                        </div>
                                    )}
                                </List.Item>
                            )}
                        />
                    )}
                </Card>
            </div>

            <div className="chat-workbench__main">
                {transportError ? <Alert type="warning" showIcon className="chat-workbench__alert" message="对话工作台提示" description={transportError} /> : null}
                {uploadError ? <Alert type="warning" showIcon className="chat-workbench__alert" message="附件上传提示" description={uploadError} /> : null}
                {knowledgeScope !== "public" && privateAttachments.length === 0 ? (
                    <Alert
                        type="info"
                        showIcon
                        className="chat-workbench__alert"
                        message="当前范围已切到知识条目 / 混合"
                        description="当前会话还没有挂接任何知识条目，因此该范围下可能检索为空。"
                    />
                ) : null}

                <Card
                    className="chat-workbench__stream-card"
                    title={activeSession?.title ?? "当前对话"}
                    extra={
                        <Space size={8} wrap className="chat-stream-toolbar">
                            <Button icon={focusModeEnabled ? <CompressOutlined /> : <ExpandOutlined />} onClick={toggleFocusMode}>
                                {focusModeEnabled ? "标准工作台" : "专注模式"}
                            </Button>
                            <Button icon={<SettingOutlined />} onClick={() => setSidePanelOpen(true)}>
                                参考资料 {currentSourceSummary.total_citation_count > 0 ? `(${currentSourceSummary.total_citation_count})` : ""}
                            </Button>
                        </Space>
                    }
                >
                    {loadingSessionDetail ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : activeSession ? (
                        <>
                            <div className="chat-stream__topline">
                                <div className="chat-stream__topline-main">
                                    <Popover trigger="click" placement="bottomLeft" content={contextDetailOverlay}>
                                        <button type="button" className="chat-context-pill">
                                            <span className="chat-context-pill__eyebrow">上下文 {contextUsagePercent}%</span>
                                            <span className="chat-context-pill__summary">{compactContextSummary}</span>
                                            <span className="chat-context-pill__meter" aria-hidden="true">
                                                <span style={{ width: `${contextUsagePercent}%` }} />
                                            </span>
                                        </button>
                                    </Popover>
                                    <Typography.Paragraph type="secondary" className="chat-context-source chat-context-source--compact">
                                        {currentContextSourceText}
                                    </Typography.Paragraph>
                                </div>
                            </div>
                            <div className="chat-message-stream">
                                {visibleMessages.length === 0 ? (
                                    <div className="chat-message-stream__empty">
                                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前会话还没有消息，先问一个双碳问题试试。" />
                                    </div>
                                ) : (
                                    visibleMessages.map((message) => (
                                        <MessageBubble
                                            key={message.message_id}
                                            message={message}
                                            sessionId={activeSession.session_id}
                                            activeCitation={message.message_id === selectedCitationMessageId}
                                            onSelectCitations={() => openCitationPanel(message.message_id)}
                                        />
                                    ))
                                )}
                                <div ref={messageStreamEndRef} />
                            </div>
                        </>
                    ) : (
                        <Empty description="当前没有可展示的会话内容。" />
                    )}
                </Card>

                <div className="chat-composer-dock">
                    <div className="chat-composer-dock__top">
                        <Typography.Text type="secondary" className="chat-composer-dock__session">
                            当前会话：{activeSession?.title ?? "未选择"}
                        </Typography.Text>
                        <Space size={8} wrap className="chat-composer-dock__chips">
                            <Tag color="blue">{scopeLabelMap[knowledgeScope]}</Tag>
                            {uploadedAttachments.length > 0 ? <Tag color="green">附件 {uploadedAttachments.length}</Tag> : null}
                            {privateAttachments.length > 0 ? <Tag color="magenta">知识条目 {privateAttachments.length}</Tag> : null}
                            {currentStreamTag ? <Tag color={currentStreamTag.color}>{currentStreamTag.label}</Tag> : null}
                            {uploading ? <Tag color="processing">正在上传附件</Tag> : null}
                        </Space>
                        <Popover trigger="click" placement="topRight" content={composerSettings}>
                            <Button icon={<MoreOutlined />}>更多设置</Button>
                        </Popover>
                    </div>
                    <div className="chat-composer-dock__main">
                        <Tooltip title="添加附件">
                            <Button icon={<PaperClipOutlined />} onClick={() => fileInputRef.current?.click()} loading={uploading} />
                        </Tooltip>
                        <Input.TextArea
                            value={question}
                            onChange={(event) => setQuestion(event.target.value)}
                            onKeyDown={handleComposerKeyDown}
                            autoSize={{ minRows: 2, maxRows: 7 }}
                            maxLength={2000}
                            autoFocus
                            placeholder="例如：结合当前知识条目，压缩空气系统的能耗问题是什么？或者：双碳目标对这家知识条目意味着什么？"
                        />
                        <Button type="primary" icon={<MessageOutlined />} onClick={handleSubmit} loading={sending}>
                            发送
                        </Button>
                    </div>
                    <input
                        ref={fileInputRef}
                        hidden
                        type="file"
                        accept=".pdf,.doc,.docx,.txt,.md,.csv,.xls,.xlsx"
                        onChange={handleUploadChange}
                    />
                </div>
            </div>

            <Drawer
                title="参考资料与状态"
                width={400}
                open={sidePanelOpen}
                onClose={() => setSidePanelOpen(false)}
            >
                <Card
                    title="当前回答依据"
                    extra={
                        <Space size={8} wrap>
                            <Tag color="green">{currentSourceSummary.total_citation_count} 条引用</Tag>
                            {currentSourceSummary.public_policy_count > 0 ? <Tag color="blue">政策 {currentSourceSummary.public_policy_count}</Tag> : null}
                            {currentSourceSummary.private_sample_count > 0 ? <Tag color="magenta">知识条目 {currentSourceSummary.private_sample_count}</Tag> : null}
                            {(currentSourceSummary.private_upload_count ?? 0) > 0 ? <Tag color="green">个人上传 {currentSourceSummary.private_upload_count ?? 0}</Tag> : null}
                        </Space>
                    }
                >
                    <Typography.Paragraph type="secondary">
                        默认只在这里展开完整引用。先读回答正文，再按需查看政策、知识条目或个人上传片段。
                    </Typography.Paragraph>
                    {selectedCitationMessage?.citations.length ? (
                        <Collapse
                            className="chat-citation-collapse"
                            ghost
                            defaultActiveKey={[]}
                            items={buildCitationCollapseItems(citationGroups)}
                        />
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选中一条带依据的助手消息后，这里会展示来源片段。" />
                    )}
                </Card>
                {isAdmin ? (
                    <Collapse
                        className="chat-side-drawer__system"
                        ghost
                        defaultActiveKey={[]}
                        items={[
                            {
                                key: "system-status",
                                label: "系统状态",
                                children: <SystemInfoPanel />,
                            },
                        ]}
                    />
                ) : null}
            </Drawer>

            <Drawer
                title="管理当前会话的知识条目挂接"
                width={420}
                open={privateSampleDrawerOpen}
                onClose={() => setPrivateSampleDrawerOpen(false)}
                extra={<Button type="primary" onClick={handleSaveAttachedSamples} loading={savingAttachedSamples}>保存挂接</Button>}
            >
                <Typography.Paragraph type="secondary">
                    这里选择的是当前会话可用于知识条目 / 混合检索的知识条目。共享样例和已入库的个人上传都会出现在这里。
                </Typography.Paragraph>
                {loadingPrivateSamples ? (
                    <div className="chat-workbench__loading"><Spin /></div>
                ) : (
                    <List
                        className="private-sample-list"
                        dataSource={knowledgeItems}
                        renderItem={(item) => {
                            const checked = draftAttachedDocIds.includes(item.knowledge_item_id);
                            return (
                                <List.Item key={item.knowledge_item_id}>
                                    <div className="private-sample-list__item">
                                        <Checkbox checked={checked} onChange={(event) => setDraftAttachedDocIds((current) => toggleDocId(current, item.knowledge_item_id, event.target.checked))}>
                                            <Typography.Text strong>{item.title}</Typography.Text>
                                        </Checkbox>
                                        <Space size={8} wrap>
                                            <Tag color="magenta">{item.source_label}</Tag>
                                            <Tag>{item.library_scope === "shared" ? "共享" : "个人"}</Tag>
                                        </Space>
                                    </div>
                                </List.Item>
                            );
                        }}
                    />
                )}
            </Drawer>
        </div>
    );
}

interface MessageBubbleProps {
    message: ChatMessageView;
    sessionId: string;
    activeCitation: boolean;
    onSelectCitations: () => void;
}

function MessageBubble({ message, sessionId, activeCitation, onSelectCitations }: MessageBubbleProps) {
    const isAssistant = message.role === "assistant";
    const isSystem = message.role === "system";
    const hasCitations = isAssistant && message.citations.length > 0;
    const messageSourceSummary = summarizeCitations(message.citations);
    const lifecycleTag = message.client_state ? lifecycleTagMap[message.client_state] : null;
    const finalStatusTag = isAssistant && isFinalAskStatus(message.status) ? statusColorMap[message.status] : null;
    const finalStatusLabel = isAssistant && isFinalAskStatus(message.status) ? statusLabelMap[message.status] : null;
    const shouldShowThinking = isAssistant && (message.client_state === "pending" || message.client_state === "thinking" || Boolean(message.thinking_content));
    const shouldShowDetails = Boolean(message.trace_id) || Boolean(message.trace_id && (!message.client_state || message.client_state === "done" || message.client_state === "error"));
    const liveStateText = message.client_state ? lifecycleStatusTextMap[message.client_state] : null;

    return (
        <div
            className={
                isAssistant
                    ? "chat-message chat-message--assistant"
                    : isSystem
                        ? "chat-message chat-message--system"
                        : "chat-message chat-message--user"
            }
        >
            <Card
                size="small"
                className={
                    isAssistant
                        ? "chat-message__card chat-message__card--assistant"
                        : isSystem
                            ? "chat-message__card chat-message__card--system"
                            : "chat-message__card chat-message__card--user"
                }
            >
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                    <Space size={8} wrap className="chat-message__header">
                        <Typography.Text className={isAssistant ? "chat-message__speaker chat-message__speaker--assistant" : isSystem ? "chat-message__speaker chat-message__speaker--system" : "chat-message__speaker chat-message__speaker--user"}>
                            {isAssistant ? "CarbonRag" : isSystem ? "系统消息" : "我"}
                        </Typography.Text>
                        {message.client_state && message.client_state !== "done" && message.client_state !== "error" ? (
                            <span className={`chat-live-state chat-live-state--${message.client_state}`}>
                                <span className="chat-live-state__dot" aria-hidden="true" />
                                <span>{liveStateText}</span>
                            </span>
                        ) : lifecycleTag ? (
                            <Tag color={lifecycleTag.color}>{lifecycleTag.label}</Tag>
                        ) : null}
                        {finalStatusTag && finalStatusLabel ? <Tag color={finalStatusTag}>{finalStatusLabel}</Tag> : null}
                        <Typography.Text type="secondary">{formatTimestamp(message.created_at)}</Typography.Text>
                    </Space>
                    {isAssistant && shouldShowThinking ? (
                        <Collapse
                            ghost
                            className="chat-message__thinking"
                            defaultActiveKey={message.client_state === "pending" || message.client_state === "thinking" ? ["thinking"] : []}
                            items={[
                                {
                                    key: "thinking",
                                    label: (
                                        <Space size={8} wrap className="chat-message__thinking-label">
                                            <span className="chat-thinking-pulse" aria-hidden="true" />
                                            <Typography.Text strong>思考中</Typography.Text>
                                            {message.client_state ? <Tag color={lifecycleTag?.color ?? "processing"}>{lifecycleTag?.label ?? "生成中"}</Tag> : null}
                                        </Space>
                                    ),
                                    children: (
                                        <Typography.Paragraph className="chat-message__thinking-content">
                            {message.thinking_content || "模型正在组织上下文与回答，请稍候。"}
                                        </Typography.Paragraph>
                                    ),
                                },
                            ]}
                        />
                    ) : null}
                    <div className={isAssistant ? "chat-message__content chat-message__content--assistant" : "chat-message__content"}>
                        {renderMessageContent(message, isAssistant)}
                    </div>
                    {isAssistant ? (
                        <div className="chat-message__meta">
                            <Space size={12} wrap>
                                {hasCitations ? (
                                    <>
                                        <Typography.Text type="secondary" className="chat-message__evidence-summary">
                                            {buildAssistantEvidenceSummary(messageSourceSummary)}
                                        </Typography.Text>
                                        <Button type={activeCitation ? "primary" : "default"} size="small" icon={<FileTextOutlined />} onClick={onSelectCitations}>
                                            查看依据 {message.citations.length}
                                        </Button>
                                    </>
                                ) : null}
                            </Space>
                            {shouldShowDetails ? (
                                <Collapse
                                    ghost
                                    className="chat-message__details"
                                    defaultActiveKey={[]}
                                    items={[
                                        {
                                            key: "details",
                                            label: "查看详细信息",
                                            children: (
                                                <Space direction="vertical" size={10} style={{ width: "100%" }}>
                                                    {message.trace_id ? (
                                                        <Typography.Text type="secondary">
                                                            追踪号：<Typography.Text code>{message.trace_id}</Typography.Text>
                                                        </Typography.Text>
                                                    ) : null}
                                                    {message.trace_id && (!message.client_state || message.client_state === "done" || message.client_state === "error") ? (
                                                        <FeedbackButtonGroup
                                                            targetType="ask"
                                                            traceId={message.trace_id}
                                                            sessionId={sessionId}
                                                            size="small"
                                                        />
                                                    ) : null}
                                                </Space>
                                            ),
                                        },
                                    ]}
                                />
                            ) : null}
                        </div>
                    ) : null}
                </Space>
            </Card>
        </div>
    );
}

interface CitationGroupProps {
    citations: AskCitation[];
}

function CitationGroup({ citations }: CitationGroupProps) {
    return (
        <div className="chat-citation-group">
            <List
                size="small"
                dataSource={citations}
                renderItem={(citation) => (
                    <List.Item key={citation.chunk_id}>
                        <div className="chat-citation-card">
                            <Space size={8} wrap>
                                <Typography.Text strong>{citation.title}</Typography.Text>
                                <Tag color={citation.source_type === "public_policy" ? "blue" : citation.source_type === "private_upload" ? "green" : "magenta"}>
                                    {citation.source_type === "public_policy" ? "公共政策" : citation.source_type === "private_upload" ? "个人上传" : "知识条目"}
                                </Tag>
                                <Tag>{citation.source}</Tag>
                                <Typography.Text type="secondary">{citation.chunk_id}</Typography.Text>
                            </Space>
                            <Typography.Paragraph className="chat-citation-card__snippet" ellipsis={{ rows: 3, expandable: "collapsible", symbol: "展开" }}>
                                {citation.snippet}
                            </Typography.Paragraph>
                            {citation.source_url ? (
                                <Typography.Link href={citation.source_url} target="_blank" rel="noreferrer">
                                    <LinkOutlined /> 查看来源
                                </Typography.Link>
                            ) : citation.source_type === "private_upload" ? (
                                <Typography.Text type="secondary">该条依据来自当前用户已入库的个人上传文档。</Typography.Text>
                            ) : (
                                <Typography.Text type="secondary">该条依据来自仓库内脱敏知识条目。</Typography.Text>
                            )}
                        </div>
                    </List.Item>
                )}
            />
        </div>
    );
}

const statusColorMap = {
    ok: "green",
    provider_error: "red",
    invalid_input: "gold",
} as const;

const statusLabelMap = {
    ok: "成功",
    provider_error: "模型服务失败",
    invalid_input: "输入无效",
} as const;

const scopeLabelMap: Record<KnowledgeScope, string> = {
    public: "公共政策",
    private_sample: "知识条目",
    mixed: "混合",
};

const compactionStatusColorMap = {
    idle: "default",
    compacted: "processing",
    failed: "error",
} as const;

const compactionStatusLabelMap = {
    idle: "当前未压缩",
    compacted: "已自动压缩",
    failed: "压缩失败",
} as const;

const lifecycleTagMap = {
    pending: { color: "default", label: "等待开始" },
    thinking: { color: "processing", label: "思考中" },
    streaming: { color: "blue", label: "正在输出" },
    done: { color: "green", label: "已完成" },
    error: { color: "red", label: "生成失败" },
} as const;

const lifecycleStatusTextMap = {
    pending: "正在建立回答位",
    thinking: "思考中",
    streaming: "正在输出",
    done: "已完成",
    error: "生成失败",
} as const;

function getAttachedPrivateSampleIds(attachedFiles: SessionAttachment[]) {
    return attachedFiles
        .filter(
            (item) =>
                item.source_type === "private_sample" ||
                item.source_type === "private_sample_repo" ||
                item.source_type === "knowledge_item",
        )
        .map((item) => item.knowledge_item_id ?? item.file_id)
        .filter((value): value is string => Boolean(value));
}

function resolvePreferredCitationMessageId(detail: SessionDetail | null): string | null {
    if (!detail) {
        return null;
    }
    const reversed = [...detail.messages].reverse();
    const latestAssistantWithCitations = reversed.find((message) => message.role === "assistant" && message.citations.length > 0);
    return latestAssistantWithCitations?.message_id ?? null;
}

function groupCitationsBySource(citations: AskCitation[]) {
    return {
        public_policy: citations.filter((item) => item.source_type === "public_policy"),
        private_sample: citations.filter((item) => item.source_type === "private_sample"),
        private_upload: citations.filter((item) => item.source_type === "private_upload"),
    };
}

function summarizeCitations(citations: AskCitation[]): AskSourceSummary {
    const groups = groupCitationsBySource(citations);
    return {
        knowledge_scope:
            groups.public_policy.length && (groups.private_sample.length || groups.private_upload.length)
                ? "mixed"
                : groups.private_sample.length || groups.private_upload.length
                    ? "private_sample"
                    : "public",
        public_policy_count: groups.public_policy.length,
        private_sample_count: groups.private_sample.length,
        private_upload_count: groups.private_upload.length,
        total_citation_count: citations.length,
    };
}

function buildPanelSourceSummary(citations: AskCitation[], fallback?: AskSourceSummary | null): AskSourceSummary {
    if (citations.length > 0) {
        return summarizeCitations(citations);
    }
    return fallback ?? {
        knowledge_scope: "public",
        public_policy_count: 0,
        private_sample_count: 0,
        private_upload_count: 0,
        total_citation_count: 0,
    };
}

function buildCitationCollapseItems(groups: ReturnType<typeof groupCitationsBySource>) {
    return [
        groups.public_policy.length
            ? {
                key: "public_policy",
                label: (
                    <Space size={8} wrap>
                        <Typography.Text strong>政策依据</Typography.Text>
                        <Tag color="blue">{groups.public_policy.length}</Tag>
                    </Space>
                ),
                children: <CitationGroup citations={groups.public_policy} />,
            }
            : null,
        groups.private_sample.length
            ? {
                key: "private_sample",
                label: (
                    <Space size={8} wrap>
                        <Typography.Text strong>共享知识依据</Typography.Text>
                        <Tag color="magenta">{groups.private_sample.length}</Tag>
                    </Space>
                ),
                children: <CitationGroup citations={groups.private_sample} />,
            }
            : null,
        groups.private_upload.length
            ? {
                key: "private_upload",
                label: (
                    <Space size={8} wrap>
                        <Typography.Text strong>个人上传依据</Typography.Text>
                        <Tag color="green">{groups.private_upload.length}</Tag>
                    </Space>
                ),
                children: <CitationGroup citations={groups.private_upload} />,
            }
            : null,
    ].filter(Boolean) as Array<{ key: string; label: any; children: any }>;
}

function buildContextSourceText(
    memoryState: SessionDetail["memory_state"],
    sourceSummary: AskSourceSummary,
    messageCount: number,
    contextSource?: StreamContextSource | null,
) {
    const parts: string[] = [];
    const recentMessageCount = contextSource?.recent_message_count ?? Math.min(6, Math.max(1, messageCount));
    const summaryPresent = contextSource?.summary_present ?? memoryState?.summary_present ?? false;
    const citationCount = contextSource?.citation_count ?? sourceSummary.total_citation_count;
    parts.push(`本轮使用最近 ${recentMessageCount} 轮消息`);

    if (summaryPresent) {
        parts.push("会话摘要");
    }

    if (citationCount > 0) {
        parts.push(`${citationCount} 条依据`);
    } else {
        parts.push("当前无额外依据");
    }

    if (summaryPresent && memoryState?.compacted_message_count) {
        parts.push(`已压缩 ${memoryState.compacted_message_count} 条更早消息`);
    }

    return parts.join(" + ");
}

function getContextUsagePercent(memoryState: SessionDetail["memory_state"]) {
    if (!memoryState || memoryState.context_budget_estimate <= 0) {
        return 0;
    }

    const percent = Math.round((memoryState.context_usage_estimate / memoryState.context_budget_estimate) * 100);
    return Math.max(0, Math.min(percent, 100));
}

function buildCompactContextSummary(
    memoryState: SessionDetail["memory_state"],
    sourceSummary: AskSourceSummary,
    contextSource?: StreamContextSource | null,
) {
    const recentMessageCount = contextSource?.recent_message_count ?? 6;
    const summaryPresent = contextSource?.summary_present ?? memoryState?.summary_present ?? false;
    const citationCount = contextSource?.citation_count ?? sourceSummary.total_citation_count;
    const parts = [`最近 ${recentMessageCount} 轮`];

    if (summaryPresent) {
        parts.push("会话摘要");
    }

    if (citationCount > 0) {
        parts.push(`${citationCount} 条依据`);
    } else {
        parts.push("无额外依据");
    }

    return parts.join(" + ");
}

function buildAssistantEvidenceSummary(sourceSummary: AskSourceSummary) {
    const parts: string[] = [];
    if (sourceSummary.public_policy_count > 0) {
        parts.push(`政策 ${sourceSummary.public_policy_count}`);
    }
    if (sourceSummary.private_sample_count > 0) {
        parts.push(`知识条目 ${sourceSummary.private_sample_count}`);
    }
    if ((sourceSummary.private_upload_count ?? 0) > 0) {
        parts.push(`个人上传 ${sourceSummary.private_upload_count ?? 0}`);
    }
    return parts.join(" · ");
}

function buildSessionRailMeta(session: SessionSummary) {
    const parts = [`更新于 ${formatTimestamp(session.updated_at)}`, `${session.message_count} 条消息`];
    if (session.file_count > 0) {
        parts.push(`${session.file_count} 个附件`);
    }
    if (session.attached_private_sample_count > 0) {
        parts.push(`${session.attached_private_sample_count} 个知识条目`);
    }
    return parts.join(" · ");
}

function resolveMessageContent(message: ChatMessageView, isAssistant: boolean) {
    if (message.content) {
        return message.content;
    }
    if (!isAssistant) {
        return "";
    }
    if (message.client_state === "pending") {
        return "正在为这条问题创建回答位…";
    }
    if (message.client_state === "thinking") {
        return "正在结合上下文与依据组织回答…";
    }
    if (message.client_state === "streaming") {
        return "正在开始输出回答…";
    }
    if (message.client_state === "error") {
        return "当前问答服务暂不可用，请稍后重试。";
    }
    return "";
}

function renderMessageContent(message: ChatMessageView, isAssistant: boolean) {
    const content = resolveMessageContent(message, isAssistant);
    if (!content) {
        return null;
    }

    if (!isAssistant) {
        return <Typography.Paragraph>{content}</Typography.Paragraph>;
    }

    return <ReactMarkdown>{content}</ReactMarkdown>;
}

function normalizeAskStreamMemoryState(memoryState: AskStreamMetadataEvent["memory_state"]): SessionDetail["memory_state"] {
    if (!memoryState || typeof memoryState !== "object") {
        return null;
    }
    if (
        typeof memoryState.context_usage_estimate !== "number" ||
        typeof memoryState.context_budget_estimate !== "number" ||
        typeof memoryState.summary_present !== "boolean" ||
        typeof memoryState.compacted_message_count !== "number"
    ) {
        return null;
    }
    if (
        memoryState.compaction_status !== "idle" &&
        memoryState.compaction_status !== "compacted" &&
        memoryState.compaction_status !== "failed"
    ) {
        return null;
    }
    return {
        context_usage_estimate: memoryState.context_usage_estimate,
        context_budget_estimate: memoryState.context_budget_estimate,
        summary_present: memoryState.summary_present,
        summary_updated_at: memoryState.summary_updated_at ?? null,
        compacted_message_count: memoryState.compacted_message_count,
        compaction_status: memoryState.compaction_status,
        summary_estimated_tokens: memoryState.summary_estimated_tokens ?? 0,
    };
}

function formatContextEstimate(value: number): string {
    if (value >= 1000) {
        return `${(value / 1000).toFixed(1)}K`;
    }
    return `${value}`;
}

function buildMemoryHint(memoryState: NonNullable<SessionDetail["memory_state"]>) {
    if (memoryState.compaction_status === "failed") {
        return "本轮旧对话压缩没有成功，系统会继续使用现有摘要和最近消息窗口回答。";
    }
    if (memoryState.summary_present) {
        return "已自动压缩旧对话，当前保留最近 6 轮完整消息，并用摘要承接更早的上下文。";
    }
    return "当前会话尚未触发自动压缩，系统会在上下文接近阈值时压缩较早对话。";
}

function toggleDocId(current: string[], target: string, checked: boolean) {
    if (checked) {
        return current.includes(target) ? current : [...current, target];
    }
    return current.filter((item) => item !== target);
}

function formatTimestamp(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString("zh-CN", {
        hour12: false,
        month: "2-digit",
        day: "2-digit",
        hour: "2-digit",
        minute: "2-digit",
    });
}

function isAskResponse(value: unknown): value is AskResponse {
    if (!value || typeof value !== "object") {
        return false;
    }
    const candidate = value as Partial<AskResponse>;
    return candidate.mode === "ask" && typeof candidate.answer === "string" && typeof candidate.trace_id === "string" && Array.isArray(candidate.citations) && typeof candidate.source_summary === "object";
}

function extractDeltaText(payload: AskStreamDeltaEvent) {
    return (payload.delta ?? payload.text ?? payload.content ?? "").trimStart();
}

function createDraftMessageId(role: "user" | "assistant") {
    if (typeof crypto !== "undefined" && "randomUUID" in crypto) {
        return `${role}-${crypto.randomUUID()}`;
    }
    return `${role}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function updateStreamDraft(current: ChatDraft | null, updater: (draft: ChatDraft) => ChatDraft) {
    if (!current) {
        return current;
    }
    return updater(current);
}

function mergeStreamMetadata(message: ChatMessageView, event: AskStreamMetadataEvent) {
    return {
        ...message,
        message_id: event.assistant_message_id ?? message.message_id,
        trace_id: event.trace_id ?? message.trace_id ?? null,
        citations: event.citations ?? message.citations,
        source_summary: event.source_summary ?? message.source_summary ?? null,
        content: typeof event.answer === "string" && event.answer ? event.answer : message.content,
        status: event.status ?? message.status ?? "ok",
    } as ChatMessageView;
}

function mapLifecycleStatusToMessageState(status: AskStreamStatusEvent["status"]) {
    switch (status) {
        case "pending":
            return { status: "pending" as const, client_state: "pending" as const };
        case "thinking":
            return { status: "thinking" as const, client_state: "thinking" as const };
        case "streaming":
            return { status: "streaming" as const, client_state: "streaming" as const };
        case "done":
            return { status: "done" as const, client_state: "done" as const };
        case "error":
            return { status: "error" as const, client_state: "error" as const };
        default:
            return { status: null, client_state: "pending" as const };
    }
}

function isFinalAskStatus(status: SessionMessage["status"]): status is AskStatus {
    return status === "ok" || status === "provider_error" || status === "invalid_input";
}

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}

function isAbortLikeError(value: unknown) {
    if (!value || typeof value !== "object") {
        return false;
    }
    const candidate = value as { name?: unknown; code?: unknown };
    return candidate.name === "AbortError" || candidate.code === "ERR_CANCELED";
}
