import {
    FileTextOutlined,
    LinkOutlined,
    MessageOutlined,
    PaperClipOutlined,
    PlusOutlined,
    TagsOutlined,
} from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Checkbox,
    Drawer,
    Empty,
    Input,
    List,
    Segmented,
    Space,
    Spin,
    Tag,
    Typography,
} from "antd";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { FeedbackButtonGroup } from "../../components/FeedbackButtonGroup";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { uploadSessionFile } from "../../services/files";
import { listPrivateSamples } from "../../services/privateSamples";
import {
    createSession,
    getSession,
    listSessions,
    replaceAttachedPrivateSamples,
    submitSessionAskRequest,
} from "../../services/sessions";
import type { AskCitation, AskResponse, AskSourceSummary, KnowledgeScope } from "../../types/ask";
import type { PrivateSampleCatalogItem } from "../../types/privateSample";
import type { SessionAttachment, SessionDetail, SessionMessage, SessionSummary } from "../../types/session";

export function AskPage() {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [selectedCitationMessageId, setSelectedCitationMessageId] = useState<string | null>(null);
    const [question, setQuestion] = useState("");
    const [knowledgeScope, setKnowledgeScope] = useState<KnowledgeScope>("public");
    const [privateSamples, setPrivateSamples] = useState<PrivateSampleCatalogItem[]>([]);
    const [privateSampleDrawerOpen, setPrivateSampleDrawerOpen] = useState(false);
    const [draftAttachedDocIds, setDraftAttachedDocIds] = useState<string[]>([]);
    const [savingAttachedSamples, setSavingAttachedSamples] = useState(false);
    const [loadingPrivateSamples, setLoadingPrivateSamples] = useState(true);
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [loadingSessionDetail, setLoadingSessionDetail] = useState(false);
    const [sending, setSending] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);

    useEffect(() => {
        void bootstrapWorkbench();
    }, []);

    useEffect(() => {
        if (!activeSessionId) {
            return;
        }
        void loadSessionDetail(activeSessionId);
    }, [activeSessionId]);

    async function bootstrapWorkbench() {
        setLoadingSessions(true);
        setLoadingPrivateSamples(true);
        setTransportError(null);

        try {
            const [sessionList, sampleCatalog] = await Promise.all([listSessions(), listPrivateSamples()]);
            setPrivateSamples(sampleCatalog);

            if (sessionList.length === 0) {
                const created = await createSession();
                setSessions([created]);
                setActiveSessionId(created.session_id);
                return;
            }

            setSessions(sessionList);
            setActiveSessionId((current) => current ?? sessionList[0].session_id);
        } catch {
            setTransportError("当前无法初始化对话工作台，请确认 backend 已启动。");
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
            const detail = await replaceAttachedPrivateSamples(activeSessionId, { doc_ids: draftAttachedDocIds });
            setActiveSession(detail);
            setDraftAttachedDocIds(getAttachedPrivateSampleIds(detail.attached_files));
            await refreshSessions(activeSessionId);
            setPrivateSampleDrawerOpen(false);
        } catch (error) {
            setTransportError(extractDetailMessage(error) ?? "当前无法保存 private sample 挂接状态。");
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

        try {
            await submitSessionAskRequest(activeSessionId, {
                question: trimmed,
                knowledge_scope: knowledgeScope,
                top_k: 5,
                attached_file_ids: knowledgeScope === "public" ? [] : draftAttachedDocIds,
            });
            setQuestion("");
            await refreshSessions(activeSessionId);
            await loadSessionDetail(activeSessionId);
        } catch (error) {
            if (isAskResponse(error)) {
                if (error.status === "invalid_input") {
                    setTransportError(error.answer);
                } else {
                    setTransportError("provider 当前响应失败，系统已把这次失败记录到当前会话。");
                    await refreshSessions(activeSessionId);
                    await loadSessionDetail(activeSessionId);
                }
            } else {
                setTransportError("当前问答服务暂不可达，请确认 backend 已启动且 provider 可用。");
            }
        } finally {
            setSending(false);
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

    const citationMessage = activeSession
        ? activeSession.messages.find((message) => message.message_id === selectedCitationMessageId)
        : null;
    const citationGroups = groupCitationsBySource(citationMessage?.citations ?? []);
    const uploadedAttachments = activeSession?.attached_files.filter((item) => item.source_type === "uploaded_file") ?? [];
    const privateAttachments = activeSession?.attached_files.filter((item) => item.source_type === "private_sample") ?? [];
    const currentSourceSummary = buildPanelSourceSummary(citationMessage?.citations ?? [], activeSession?.source_summary);

    return (
        <div className="chat-workbench">
            <div className="chat-workbench__sidebar">
                <Card
                    title="会话列表"
                    extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>新建对话</Button>}
                >
                    <Typography.Paragraph type="secondary">
                        v0.1.8 继续沿用 conversation workbench，并把 private sample / mixed scope 接入当前 ask。
                    </Typography.Paragraph>
                    {loadingSessions ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : (
                        <List
                            className="chat-session-list"
                            dataSource={sessions}
                            locale={{ emptyText: "当前还没有会话。" }}
                            renderItem={(session) => (
                                <List.Item
                                    className={activeSessionId === session.session_id ? "chat-session-list__item chat-session-list__item--active" : "chat-session-list__item"}
                                    onClick={() => setActiveSessionId(session.session_id)}
                                >
                                    <div className="chat-session-list__content">
                                        <Typography.Text strong>{session.title}</Typography.Text>
                                        <Typography.Text type="secondary">{formatTimestamp(session.updated_at)}</Typography.Text>
                                        <Space size={8} wrap>
                                            <Tag>{session.message_count} 条消息</Tag>
                                            <Tag>{session.file_count} 个上传附件</Tag>
                                            <Tag color="magenta">{session.attached_private_sample_count} 个样例</Tag>
                                        </Space>
                                    </div>
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
                        message="当前 scope 已切到 private sample / mixed"
                        description="当前会话还没有挂接任何脱敏企业样例，因此该 scope 下可能检索为空。"
                    />
                ) : null}

                <Card
                    className="chat-workbench__stream-card"
                    title="消息流"
                    extra={
                        <Space size={8} wrap>
                            <Tag color="blue">{scopeLabelMap[knowledgeScope]}</Tag>
                            <Tag color="green">{uploadedAttachments.length} 个上传附件</Tag>
                            <Tag color="magenta">{privateAttachments.length} 个样例挂接</Tag>
                        </Space>
                    }
                >
                    {loadingSessionDetail ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : activeSession ? (
                        <>
                            <Typography.Paragraph type="secondary">
                                当前 ask 会带最近 4 轮历史继续回答；scope 可切到 public、private sample 或 mixed。
                            </Typography.Paragraph>
                            <div className="chat-message-stream">
                                {activeSession.messages.length === 0 ? (
                                    <div className="chat-message-stream__empty">
                                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前会话还没有消息，先问一个双碳问题试试。" />
                                    </div>
                                ) : (
                                    activeSession.messages.map((message) => (
                                        <MessageBubble
                                            key={message.message_id}
                                            message={message}
                                            sessionId={activeSession.session_id}
                                            activeCitation={message.message_id === selectedCitationMessageId}
                                            onSelectCitations={() => setSelectedCitationMessageId(message.message_id)}
                                        />
                                    ))
                                )}
                            </div>
                        </>
                    ) : (
                        <Empty description="当前没有可展示的会话内容。" />
                    )}
                </Card>

                <Card className="chat-workbench__composer-card" title="输入区">
                    <div className="chat-scope-bar">
                        <Segmented<KnowledgeScope>
                            block
                            value={knowledgeScope}
                            onChange={(value) => setKnowledgeScope(value)}
                            options={[
                                { label: "public", value: "public" },
                                { label: "private sample", value: "private_sample" },
                                { label: "mixed", value: "mixed" },
                            ]}
                        />
                        <Typography.Paragraph type="secondary" className="chat-scope-bar__hint">
                            public 只看政策样本；private sample 只看当前会话已挂接的脱敏企业样例；mixed 同时参考两类依据。
                        </Typography.Paragraph>
                    </div>

                    <div className="chat-session-state">
                        <Tag color="blue">当前 scope：{scopeLabelMap[knowledgeScope]}</Tag>
                        <Tag color="green">上传附件：{uploadedAttachments.length}</Tag>
                        <Tag color="magenta">挂接样例：{privateAttachments.length}</Tag>
                        <Button icon={<TagsOutlined />} onClick={() => setPrivateSampleDrawerOpen(true)} disabled={loadingPrivateSamples}>
                            管理样例挂接
                        </Button>
                    </div>

                    <Typography.Paragraph type="secondary">
                        当前上传入口继续只做 session 绑定；上传文件不会进入 ask 检索。本轮 private retrieval 只读取仓库内的脱敏样例。
                    </Typography.Paragraph>

                    {activeSession?.attached_files.length ? (
                        <div className="chat-attachments">
                            {activeSession.attached_files.map((file) => (
                                <Tag
                                    key={`${file.source_type}-${file.file_id}`}
                                    icon={file.source_type === "private_sample" ? <TagsOutlined /> : <PaperClipOutlined />}
                                    className="chat-attachments__tag"
                                    color={file.source_type === "private_sample" ? "magenta" : undefined}
                                >
                                    {file.filename}
                                </Tag>
                            ))}
                        </div>
                    ) : null}

                    <Input.TextArea
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        rows={5}
                        maxLength={2000}
                        placeholder="例如：结合当前样例，压缩空气系统的能耗问题是什么？或者：双碳目标对这家样例企业意味着什么？"
                    />
                    <Space className="chat-composer__actions" size={12} wrap>
                        <Button icon={<PaperClipOutlined />} onClick={() => fileInputRef.current?.click()} loading={uploading}>添加附件</Button>
                        <Button type="primary" icon={<MessageOutlined />} onClick={handleSubmit} loading={sending}>发送到当前会话</Button>
                        <Typography.Text type="secondary">当前 session：{activeSession?.title ?? "未选择"}</Typography.Text>
                    </Space>
                    <input
                        ref={fileInputRef}
                        hidden
                        type="file"
                        accept=".pdf,.doc,.docx,.txt,.md,.csv,.xls,.xlsx"
                        onChange={handleUploadChange}
                    />
                </Card>
            </div>

            <div className="chat-workbench__panel">
                <Card
                    title="依据面板"
                    extra={
                        <Space size={8} wrap>
                            <Tag color="green">{currentSourceSummary.total_citation_count} 条依据</Tag>
                            <Tag color="blue">{currentSourceSummary.public_policy_count} 条政策</Tag>
                            <Tag color="magenta">{currentSourceSummary.private_sample_count} 条样例</Tag>
                        </Space>
                    }
                >
                    <Typography.Paragraph type="secondary">
                        当前 citations 来自本地公共政策样本与脱敏企业样例。private sample 不代表真实客户审计结果。
                    </Typography.Paragraph>
                    {citationMessage?.citations.length ? (
                        <div className="chat-citation-groups">
                            {citationGroups.public_policy.length ? <CitationGroup title="政策依据" tagColor="blue" citations={citationGroups.public_policy} /> : null}
                            {citationGroups.private_sample.length ? <CitationGroup title="企业样例依据" tagColor="magenta" citations={citationGroups.private_sample} /> : null}
                        </div>
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选中一条带依据的助手消息后，这里会展示来源片段。" />
                    )}
                </Card>
                <SystemInfoPanel />
            </div>

            <Drawer
                title="管理当前会话的 private sample 挂接"
                width={420}
                open={privateSampleDrawerOpen}
                onClose={() => setPrivateSampleDrawerOpen(false)}
                extra={<Button type="primary" onClick={handleSaveAttachedSamples} loading={savingAttachedSamples}>保存挂接</Button>}
            >
                <Typography.Paragraph type="secondary">
                    这里选择的是当前 session 可用于 private_sample / mixed 检索的脱敏样例。上传文件不会自动进入这一列表。
                </Typography.Paragraph>
                {loadingPrivateSamples ? (
                    <div className="chat-workbench__loading"><Spin /></div>
                ) : (
                    <List
                        className="private-sample-list"
                        dataSource={privateSamples}
                        renderItem={(item) => {
                            const checked = draftAttachedDocIds.includes(item.doc_id);
                            return (
                                <List.Item key={item.doc_id}>
                                    <div className="private-sample-list__item">
                                        <Checkbox checked={checked} onChange={(event) => setDraftAttachedDocIds((current) => toggleDocId(current, item.doc_id, event.target.checked))}>
                                            <Typography.Text strong>{item.title}</Typography.Text>
                                        </Checkbox>
                                        <Space size={8} wrap>
                                            <Tag color="magenta">{item.sample_type}</Tag>
                                            <Tag>{item.business_topic}</Tag>
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
    message: SessionMessage;
    sessionId: string;
    activeCitation: boolean;
    onSelectCitations: () => void;
}

function MessageBubble({ message, sessionId, activeCitation, onSelectCitations }: MessageBubbleProps) {
    const isAssistant = message.role === "assistant";
    const isSystem = message.role === "system";
    const hasCitations = isAssistant && message.citations.length > 0;
    const messageSourceSummary = summarizeCitations(message.citations);

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
                        ? "chat-message__card"
                        : isSystem
                            ? "chat-message__card chat-message__card--system"
                            : "chat-message__card chat-message__card--user"
                }
            >
                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                    <Space size={8} wrap>
                        <Tag color={isAssistant ? "blue" : isSystem ? "purple" : "gold"}>
                            {isAssistant ? "助手" : isSystem ? "系统" : "用户"}
                        </Tag>
                        {isAssistant && message.status ? <Tag color={statusColorMap[message.status]}>{message.status}</Tag> : null}
                        <Typography.Text type="secondary">{formatTimestamp(message.created_at)}</Typography.Text>
                    </Space>
                    <Typography.Paragraph className="chat-message__content">{message.content}</Typography.Paragraph>
                    {isAssistant ? (
                        <Space size={12} wrap>
                            {message.trace_id ? (
                                <Typography.Text type="secondary">
                                    Trace: <Typography.Text code>{message.trace_id}</Typography.Text>
                                </Typography.Text>
                            ) : null}
                            {isAssistant && message.trace_id ? (
                                <FeedbackButtonGroup
                                    targetType="ask"
                                    traceId={message.trace_id}
                                    sessionId={sessionId}
                                    size="small"
                                />
                            ) : null}
                            {hasCitations ? (
                                <>
                                    <Tag color="blue">{messageSourceSummary.public_policy_count} 条政策</Tag>
                                    <Tag color="magenta">{messageSourceSummary.private_sample_count} 条样例</Tag>
                                    <Button type={activeCitation ? "primary" : "default"} size="small" icon={<FileTextOutlined />} onClick={onSelectCitations}>
                                        查看依据 {message.citations.length}
                                    </Button>
                                </>
                            ) : null}
                        </Space>
                    ) : null}
                </Space>
            </Card>
        </div>
    );
}

interface CitationGroupProps {
    title: string;
    tagColor: string;
    citations: AskCitation[];
}

function CitationGroup({ title, tagColor, citations }: CitationGroupProps) {
    return (
        <div className="chat-citation-group">
            <Space size={8} wrap className="chat-citation-group__header">
                <Typography.Text strong>{title}</Typography.Text>
                <Tag color={tagColor}>{citations.length}</Tag>
            </Space>
            <List
                dataSource={citations}
                renderItem={(citation) => (
                    <List.Item key={citation.chunk_id}>
                        <div className="chat-citation-card">
                            <Space size={8} wrap>
                                <Typography.Text strong>{citation.title}</Typography.Text>
                                <Tag color={citation.source_type === "public_policy" ? "blue" : "magenta"}>
                                    {citation.source_type === "public_policy" ? "public policy" : "private sample"}
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
                            ) : (
                                <Typography.Text type="secondary">该条依据来自仓库内脱敏企业样例。</Typography.Text>
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

const scopeLabelMap: Record<KnowledgeScope, string> = {
    public: "public",
    private_sample: "private sample",
    mixed: "mixed",
};

function getAttachedPrivateSampleIds(attachedFiles: SessionAttachment[]) {
    return attachedFiles.filter((item) => item.source_type === "private_sample").map((item) => item.file_id);
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
    };
}

function summarizeCitations(citations: AskCitation[]): AskSourceSummary {
    const groups = groupCitationsBySource(citations);
    return {
        knowledge_scope: groups.public_policy.length && groups.private_sample.length ? "mixed" : groups.private_sample.length ? "private_sample" : "public",
        public_policy_count: groups.public_policy.length,
        private_sample_count: groups.private_sample.length,
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
        total_citation_count: 0,
    };
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

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
