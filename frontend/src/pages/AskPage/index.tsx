import {
    FileTextOutlined,
    LinkOutlined,
    MessageOutlined,
    PaperClipOutlined,
    PlusOutlined,
} from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Empty,
    Input,
    List,
    Space,
    Spin,
    Tag,
    Typography,
} from "antd";
import { useEffect, useRef, useState } from "react";
import type { ChangeEvent } from "react";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { uploadSessionFile } from "../../services/files";
import {
    createSession,
    getSession,
    listSessions,
    submitSessionAskRequest,
} from "../../services/sessions";
import type { AskResponse } from "../../types/ask";
import type { SessionDetail, SessionMessage, SessionSummary } from "../../types/session";

export function AskPage() {
    const fileInputRef = useRef<HTMLInputElement | null>(null);
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [selectedCitationMessageId, setSelectedCitationMessageId] = useState<string | null>(null);
    const [question, setQuestion] = useState("");
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [loadingSessionDetail, setLoadingSessionDetail] = useState(false);
    const [sending, setSending] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);
    const [uploadError, setUploadError] = useState<string | null>(null);

    useEffect(() => {
        void bootstrapSessions();
    }, []);

    useEffect(() => {
        if (!activeSessionId) {
            return;
        }
        void loadSessionDetail(activeSessionId);
    }, [activeSessionId]);

    async function bootstrapSessions() {
        setLoadingSessions(true);
        setTransportError(null);

        try {
            const sessionList = await listSessions();
            if (sessionList.length === 0) {
                const created = await createSession();
                setSessions([created]);
                setActiveSessionId(created.session_id);
                return;
            }

            setSessions(sessionList);
            setActiveSessionId((current) => current ?? sessionList[0].session_id);
        } catch {
            setTransportError("当前无法初始化会话列表，请确认 backend 已启动。");
        } finally {
            setLoadingSessions(false);
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
            await refreshSessions(created.session_id);
        } catch {
            setTransportError("当前无法创建新会话，请稍后重试。");
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
                knowledge_scope: "public",
                top_k: 5,
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

    return (
        <div className="chat-workbench">
            <div className="chat-workbench__sidebar">
                <Card
                    title="会话列表"
                    extra={
                        <Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>
                            新建对话
                        </Button>
                    }
                >
                    <Typography.Paragraph type="secondary">
                        v0.1.7 开始把 ask 从单轮表单推进到最小可用对话工作台。
                    </Typography.Paragraph>
                    {loadingSessions ? (
                        <div className="chat-workbench__loading">
                            <Spin />
                        </div>
                    ) : (
                        <List
                            className="chat-session-list"
                            dataSource={sessions}
                            locale={{ emptyText: "当前还没有会话。" }}
                            renderItem={(session) => (
                                <List.Item
                                    className={
                                        activeSessionId === session.session_id
                                            ? "chat-session-list__item chat-session-list__item--active"
                                            : "chat-session-list__item"
                                    }
                                    onClick={() => setActiveSessionId(session.session_id)}
                                >
                                    <div className="chat-session-list__content">
                                        <Typography.Text strong>{session.title}</Typography.Text>
                                        <Typography.Text type="secondary">
                                            {formatTimestamp(session.updated_at)}
                                        </Typography.Text>
                                        <Space size={8} wrap>
                                            <Tag>{session.message_count} 条消息</Tag>
                                            <Tag>{session.file_count} 个附件</Tag>
                                        </Space>
                                    </div>
                                </List.Item>
                            )}
                        />
                    )}
                </Card>
            </div>

            <div className="chat-workbench__main">
                {transportError ? (
                    <Alert
                        type="warning"
                        showIcon
                        className="chat-workbench__alert"
                        message="会话工作台提示"
                        description={transportError}
                    />
                ) : null}
                {uploadError ? (
                    <Alert
                        type="warning"
                        showIcon
                        className="chat-workbench__alert"
                        message="附件上传提示"
                        description={uploadError}
                    />
                ) : null}

                <Card
                    className="chat-workbench__stream-card"
                    title="消息流"
                    extra={<Tag color="blue">public policy grounding</Tag>}
                >
                    {loadingSessionDetail ? (
                        <div className="chat-workbench__loading">
                            <Spin />
                        </div>
                    ) : activeSession ? (
                        <>
                            <Typography.Paragraph type="secondary">
                                当前会话会带最近 4 轮历史继续 ask，上下文仍只允许 `knowledge_scope=public`。
                            </Typography.Paragraph>
                            <div className="chat-message-stream">
                                {activeSession.messages.length === 0 ? (
                                    <div className="chat-message-stream__empty">
                                        <Empty
                                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                                            description="当前会话还没有消息，先问一个双碳问题试试。"
                                        />
                                    </div>
                                ) : (
                                    activeSession.messages.map((message) => (
                                        <MessageBubble
                                            key={message.message_id}
                                            message={message}
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
                    <Typography.Paragraph type="secondary">
                        当前上传入口只做骨架：附件会绑定到当前 session 并显示出来，但不会进入 ask 推理。
                    </Typography.Paragraph>
                    {activeSession?.files.length ? (
                        <div className="chat-attachments">
                            {activeSession.files.map((file) => (
                                <Tag key={file.file_id} icon={<PaperClipOutlined />} className="chat-attachments__tag">
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
                        placeholder="例如：什么是双碳目标？继续追问时，会带上当前 session 的最近对话历史。"
                    />
                    <Space className="chat-composer__actions" size={12} wrap>
                        <Button
                            icon={<PaperClipOutlined />}
                            onClick={() => fileInputRef.current?.click()}
                            loading={uploading}
                        >
                            添加附件
                        </Button>
                        <Button
                            type="primary"
                            icon={<MessageOutlined />}
                            onClick={handleSubmit}
                            loading={sending}
                        >
                            发送到当前会话
                        </Button>
                        <Typography.Text type="secondary">
                            当前 session：{activeSession?.title ?? "未选择"}
                        </Typography.Text>
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
                        citationMessage?.citations.length ? (
                            <Tag color="green">{citationMessage.citations.length} 条依据</Tag>
                        ) : null
                    }
                >
                    {citationMessage?.citations.length ? (
                        <List
                            dataSource={citationMessage.citations}
                            renderItem={(citation) => (
                                <List.Item key={citation.chunk_id}>
                                    <div className="chat-citation-card">
                                        <Space size={8} wrap>
                                            <Typography.Text strong>{citation.title}</Typography.Text>
                                            <Tag>{citation.source}</Tag>
                                            <Typography.Text type="secondary">{citation.chunk_id}</Typography.Text>
                                        </Space>
                                        <Typography.Paragraph className="chat-citation-card__snippet">
                                            {citation.snippet}
                                        </Typography.Paragraph>
                                        <Typography.Link href={citation.source_url} target="_blank" rel="noreferrer">
                                            <LinkOutlined /> 查看来源
                                        </Typography.Link>
                                    </div>
                                </List.Item>
                            )}
                        />
                    ) : (
                        <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description="选中一条带依据的助手消息后，这里会展示来源片段。"
                        />
                    )}
                </Card>
                <SystemInfoPanel />
            </div>
        </div>
    );
}

interface MessageBubbleProps {
    message: SessionMessage;
    activeCitation: boolean;
    onSelectCitations: () => void;
}

function MessageBubble({ message, activeCitation, onSelectCitations }: MessageBubbleProps) {
    const isAssistant = message.role === "assistant";
    const hasCitations = isAssistant && message.citations.length > 0;

    return (
        <div
            className={
                isAssistant
                    ? "chat-message chat-message--assistant"
                    : "chat-message chat-message--user"
            }
        >
            <Card
                size="small"
                className={isAssistant ? "chat-message__card" : "chat-message__card chat-message__card--user"}
            >
                <Space direction="vertical" size={8} style={{ width: "100%" }}>
                    <Space size={8} wrap>
                        <Tag color={isAssistant ? "blue" : "gold"}>
                            {isAssistant ? "助手" : "用户"}
                        </Tag>
                        {isAssistant && message.status ? (
                            <Tag color={statusColorMap[message.status]}>{message.status}</Tag>
                        ) : null}
                        <Typography.Text type="secondary">{formatTimestamp(message.created_at)}</Typography.Text>
                    </Space>
                    <Typography.Paragraph className="chat-message__content">
                        {message.content}
                    </Typography.Paragraph>
                    {isAssistant ? (
                        <Space size={12} wrap>
                            {message.trace_id ? (
                                <Typography.Text type="secondary">
                                    Trace: <Typography.Text code>{message.trace_id}</Typography.Text>
                                </Typography.Text>
                            ) : null}
                            {hasCitations ? (
                                <Button
                                    type={activeCitation ? "primary" : "default"}
                                    size="small"
                                    icon={<FileTextOutlined />}
                                    onClick={onSelectCitations}
                                >
                                    查看依据 {message.citations.length}
                                </Button>
                            ) : null}
                        </Space>
                    ) : null}
                </Space>
            </Card>
        </div>
    );
}

const statusColorMap = {
    ok: "green",
    provider_error: "red",
    invalid_input: "gold",
} as const;

function resolvePreferredCitationMessageId(detail: SessionDetail | null): string | null {
    if (!detail) {
        return null;
    }
    const reversed = [...detail.messages].reverse();
    const latestAssistantWithCitations = reversed.find(
        (message) => message.role === "assistant" && message.citations.length > 0,
    );
    return latestAssistantWithCitations?.message_id ?? null;
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
    return (
        candidate.mode === "ask" &&
        typeof candidate.answer === "string" &&
        typeof candidate.trace_id === "string" &&
        Array.isArray(candidate.citations)
    );
}

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }

    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
