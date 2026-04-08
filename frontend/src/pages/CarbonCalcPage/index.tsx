import { ExperimentOutlined, FileTextOutlined, PlusOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Descriptions,
    Empty,
    Input,
    InputNumber,
    List,
    Space,
    Spin,
    Statistic,
    Tag,
    Typography,
} from "antd";
import { useEffect, useState } from "react";
import { FeedbackButtonGroup } from "../../components/FeedbackButtonGroup";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { submitCarbonCalculation } from "../../services/carbon";
import { createSession, getSession, listSessions } from "../../services/sessions";
import type { CalcCarbonResponse } from "../../types/carbon";
import type { SessionDetail, SessionSummary } from "../../types/session";

interface CarbonFormState {
    period_label: string;
    electricity_kwh: number;
    natural_gas_m3: number;
    diesel_l: number;
}

const initialFormState: CarbonFormState = {
    period_label: "",
    electricity_kwh: 0,
    natural_gas_m3: 0,
    diesel_l: 0,
};

export function CarbonCalcPage() {
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [formState, setFormState] = useState<CarbonFormState>(initialFormState);
    const [calcResult, setCalcResult] = useState<CalcCarbonResponse | null>(null);
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [loadingSessionDetail, setLoadingSessionDetail] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);

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
            setTransportError("当前无法初始化碳核算工作台，请确认 backend 已启动。");
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
        } catch {
            setActiveSession(null);
            setTransportError("当前无法读取选中的会话，请稍后重试。");
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
        setSubmitting(true);
        setTransportError(null);
        try {
            const response = await submitCarbonCalculation({
                session_id: activeSessionId ?? undefined,
                period_label: formState.period_label.trim() || undefined,
                electricity_kwh: formState.electricity_kwh,
                natural_gas_m3: formState.natural_gas_m3,
                diesel_l: formState.diesel_l,
            });
            setCalcResult(response);
            if (activeSessionId) {
                await refreshSessions(activeSessionId);
                await loadSessionDetail(activeSessionId);
            }
        } catch (error) {
            setCalcResult(null);
            setTransportError(extractDetailMessage(error) ?? "当前碳核算服务暂不可用，请稍后重试。");
        } finally {
            setSubmitting(false);
        }
    }

    const uploadedFileCount = activeSession?.attached_files.filter((item) => item.source_type === "uploaded_file").length ?? 0;
    const privateSampleCount = activeSession?.attached_files.filter((item) => item.source_type === "private_sample").length ?? 0;

    return (
        <div className="chat-workbench">
            <div className="chat-workbench__sidebar">
                <Card
                    title="会话列表"
                    extra={<Button type="primary" icon={<PlusOutlined />} onClick={handleCreateSession}>新建对话</Button>}
                >
                    <Typography.Paragraph type="secondary">
                        v0.1.9A 在当前 conversation workbench 上新增真实碳核算链路，并把结果与反馈落入本地数据库。
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
                                            <Tag>{session.file_count} 个附件</Tag>
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
                {transportError ? (
                    <Alert
                        type="warning"
                        showIcon
                        className="chat-workbench__alert"
                        message="碳核算提示"
                        description={transportError}
                    />
                ) : null}

                <Card
                    className="calc-workbench__form-card"
                    title="碳核算输入"
                    extra={<Tag color="blue">{activeSession?.title ?? "未选择会话"}</Tag>}
                >
                    <Typography.Paragraph type="secondary">
                        本轮只支持购电量、天然气用量和柴油用量三类活动数据；结果会关联到当前 session，但不会进入 ask 消息流。
                    </Typography.Paragraph>
                    <div className="chat-session-state">
                        <Tag color="blue">当前 session：{activeSession ? "已关联" : "未关联"}</Tag>
                        <Tag color="green">上传附件：{uploadedFileCount}</Tag>
                        <Tag color="magenta">挂接样例：{privateSampleCount}</Tag>
                    </div>

                    <div className="calc-form-grid">
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>期间标签</Typography.Text>
                            <Input
                                value={formState.period_label}
                                onChange={(event) => setFormState((current) => ({ ...current, period_label: event.target.value }))}
                                placeholder="例如：2026-Q1"
                            />
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>购电量 (kWh)</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.electricity_kwh}
                                onChange={(value) => setFormState((current) => ({ ...current, electricity_kwh: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>天然气用量 (m3)</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.natural_gas_m3}
                                onChange={(value) => setFormState((current) => ({ ...current, natural_gas_m3: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>柴油用量 (L)</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.diesel_l}
                                onChange={(value) => setFormState((current) => ({ ...current, diesel_l: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                        </div>
                    </div>

                    <Space size={12} wrap className="chat-composer__actions">
                        <Button
                            type="primary"
                            icon={<ExperimentOutlined />}
                            loading={submitting}
                            onClick={() => void handleSubmit()}
                        >
                            计算当前排放
                        </Button>
                        <Typography.Text type="secondary">
                            当前结果将{activeSessionId ? "关联到选中的 session" : "不关联 session"}
                        </Typography.Text>
                    </Space>
                </Card>

                <Card
                    className="calc-workbench__result-card"
                    title="核算结果"
                    extra={calcResult ? <Tag color="green">Trace {calcResult.trace_id}</Tag> : null}
                >
                    {loadingSessionDetail && !calcResult ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : calcResult ? (
                        <div className="calc-result-stack">
                            <div className="calc-result-summary">
                                <Statistic
                                    title="总排放量"
                                    value={calcResult.total_emission_kgco2e}
                                    precision={3}
                                    suffix="kgCO2e"
                                />
                                <Space size={12} wrap>
                                    <Tag color={activeSessionId ? "blue" : "default"}>
                                        {activeSessionId ? `已关联到 ${activeSession?.title ?? activeSessionId}` : "未关联 session"}
                                    </Tag>
                                    <FeedbackButtonGroup
                                        targetType="calc_carbon"
                                        traceId={calcResult.trace_id}
                                        sessionId={activeSessionId}
                                        size="middle"
                                    />
                                </Space>
                            </div>

                            <Descriptions title="公式说明" bordered column={1} size="small">
                                <Descriptions.Item label="摘要">{calcResult.formula_summary}</Descriptions.Item>
                            </Descriptions>

                            <Card size="small" title="分项 breakdown">
                                <List
                                    dataSource={calcResult.breakdown}
                                    renderItem={(item) => (
                                        <List.Item key={item.item}>
                                            <div className="calc-breakdown-row">
                                                <div>
                                                    <Typography.Text strong>{itemLabelMap[item.item]}</Typography.Text>
                                                    <Typography.Paragraph type="secondary" className="calc-breakdown-row__meta">
                                                        {item.activity_value} {item.activity_unit} × {item.factor_value} {item.factor_unit}
                                                    </Typography.Paragraph>
                                                </div>
                                                <Tag color="green">{item.emission_kgco2e} kgCO2e</Tag>
                                            </div>
                                        </List.Item>
                                    )}
                                />
                            </Card>
                        </div>
                    ) : (
                        <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description="提交活动数据后，这里会显示总排放量、分项结果和因子来源。"
                        />
                    )}
                </Card>
            </div>

            <div className="chat-workbench__panel">
                <Card
                    title="因子依据"
                    extra={calcResult ? <Tag color="green">{calcResult.citations.length} 条来源</Tag> : null}
                >
                    <Typography.Paragraph type="secondary">
                        当前使用的是 v0.1.9A 本地 demo 因子基线。来源信息用于前端展示与回溯，不代表正式盘查口径。
                    </Typography.Paragraph>
                    {calcResult?.citations.length ? (
                        <List
                            dataSource={calcResult.citations}
                            renderItem={(citation) => (
                                <List.Item key={citation.factor_id}>
                                    <div className="chat-citation-card">
                                        <Space size={8} wrap>
                                            <Typography.Text strong>{citation.factor_id}</Typography.Text>
                                            <Tag color="gold">factor</Tag>
                                        </Space>
                                        <Typography.Paragraph className="chat-citation-card__snippet">
                                            {citation.source}
                                        </Typography.Paragraph>
                                        <Typography.Link href={citation.source_url} target="_blank" rel="noreferrer">
                                            <FileTextOutlined /> 查看来源
                                        </Typography.Link>
                                    </div>
                                </List.Item>
                            )}
                        />
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="完成一次核算后，这里会显示因子来源。" />
                    )}
                </Card>
                <SystemInfoPanel />
            </div>
        </div>
    );
}

const itemLabelMap = {
    electricity: "购电量",
    natural_gas: "天然气",
    diesel: "柴油",
} as const;

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

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
