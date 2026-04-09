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
import { listAttachableKnowledgeItems, replaceAttachedKnowledgeItems } from "../../services/knowledge";
import {
    createSession,
    getSession,
    listSessions,
    submitSessionAskRequest,
} from "../../services/sessions";
import type { AskCitation, AskResponse, AskSourceSummary, KnowledgeScope } from "../../types/ask";
import type { KnowledgeItem } from "../../types/knowledge";
import type { SessionAttachment, SessionDetail, SessionMessage, SessionSummary } from "../../types/session";

export function AskPage() {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [selectedCitationMessageId, setSelectedCitationMessageId] = useState<string | null>(null);
    const [question, setQuestion] = useState("");
    const [knowledgeScope, setKnowledgeScope] = useState<KnowledgeScope>("public");
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
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
                    setTransportError("模型服务当前响应失败，系统已把这次失败记录到当前会话。");
                    await refreshSessions(activeSessionId);
                    await loadSessionDetail(activeSessionId);
                }
            } else {
                setTransportError("当前问答服务暂不可达，请确认后端已启动且模型服务可用。");
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
                        V1.1.0 继续沿用对话工作台，并把知识条目 / 混合范围接入当前问答。
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
                                            <Tag color="magenta">{session.attached_private_sample_count} 个知识条目</Tag>
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
                        message="当前范围已切到知识条目 / 混合"
                        description="当前会话还没有挂接任何知识条目，因此该范围下可能检索为空。"
                    />
                ) : null}

                <Card
                    className="chat-workbench__stream-card"
                    title="消息流"
                    extra={
                        <Space size={8} wrap>
                            <Tag color="blue">{scopeLabelMap[knowledgeScope]}</Tag>
                            <Tag color="green">{uploadedAttachments.length} 个上传附件</Tag>
                            <Tag color="magenta">{privateAttachments.length} 个知识条目挂接</Tag>
                        </Space>
                    }
                >
                    {loadingSessionDetail ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : activeSession ? (
                        <>
                            <Typography.Paragraph type="secondary">
                                当前问答会带最近 4 轮历史继续回答；范围可切到公共政策、知识条目或混合模式。
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
                                { label: "公共政策", value: "public" },
                                { label: "知识条目", value: "private_sample" },
                                { label: "混合", value: "mixed" },
                            ]}
                        />
                        <Typography.Paragraph type="secondary" className="chat-scope-bar__hint">
                            公共政策只看政策样本；知识条目只看当前会话已挂接的脱敏知识条目；混合模式同时参考两类依据。
                        </Typography.Paragraph>
                    </div>

                    <div className="chat-session-state">
                        <Tag color="blue">当前范围：{scopeLabelMap[knowledgeScope]}</Tag>
                        <Tag color="green">上传附件：{uploadedAttachments.length}</Tag>
                        <Tag color="magenta">挂接知识条目：{privateAttachments.length}</Tag>
                        <Button icon={<TagsOutlined />} onClick={() => setPrivateSampleDrawerOpen(true)} disabled={loadingPrivateSamples}>
                            管理知识条目挂接
                        </Button>
                    </div>

                    <Typography.Paragraph type="secondary">
                        上传文件会进入知识任务流；只有索引完成并挂接到当前会话后，才会参与知识条目 / 混合检索。
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
                        placeholder="例如：结合当前知识条目，压缩空气系统的能耗问题是什么？或者：双碳目标对这家知识条目意味着什么？"
                    />
                    <Space className="chat-composer__actions" size={12} wrap>
                        <Button icon={<PaperClipOutlined />} onClick={() => fileInputRef.current?.click()} loading={uploading}>添加附件</Button>
                        <Button type="primary" icon={<MessageOutlined />} onClick={handleSubmit} loading={sending}>发送到当前会话</Button>
                        <Typography.Text type="secondary">当前会话：{activeSession?.title ?? "未选择"}</Typography.Text>
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
                            <Tag color="magenta">{currentSourceSummary.private_sample_count} 条知识条目</Tag>
                        </Space>
                    }
                >
                <Typography.Paragraph type="secondary">
                    当前依据来自本地公共政策样本、管理员共享知识条目和当前用户已挂接的个人上传知识。私有知识条目不代表真实客户审计结果。
                </Typography.Paragraph>
                    {citationMessage?.citations.length ? (
                        <div className="chat-citation-groups">
                            {citationGroups.public_policy.length ? <CitationGroup title="政策依据" tagColor="blue" citations={citationGroups.public_policy} /> : null}
                            {citationGroups.private_sample.length ? <CitationGroup title="共享知识依据" tagColor="magenta" citations={citationGroups.private_sample} /> : null}
                            {citationGroups.private_upload.length ? <CitationGroup title="个人上传依据" tagColor="green" citations={citationGroups.private_upload} /> : null}
                        </div>
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选中一条带依据的助手消息后，这里会展示来源片段。" />
                    )}
                </Card>
                <SystemInfoPanel />
            </div>

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
                                    追踪号：<Typography.Text code>{message.trace_id}</Typography.Text>
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
                                    <Tag color="magenta">{messageSourceSummary.private_sample_count} 条知识条目</Tag>
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
                                    {citation.source_type === "public_policy" ? "公共政策" : "知识条目"}
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

const scopeLabelMap: Record<KnowledgeScope, string> = {
    public: "公共政策",
    private_sample: "知识条目",
    mixed: "混合",
};

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
