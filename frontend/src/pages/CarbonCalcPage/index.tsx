import { ExperimentOutlined, FileTextOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Collapse,
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
import { useWorkbenchShellContext } from "../../layouts/WorkbenchShellContext";
import { submitCarbonCalculation } from "../../services/carbon";
import { getSession } from "../../services/sessions";
import type { CalcCarbonResponse } from "../../types/carbon";
import type { SessionDetail } from "../../types/session";

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
    const { activeSessionId, refreshSessions } = useWorkbenchShellContext();
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [formState, setFormState] = useState<CarbonFormState>(initialFormState);
    const [calcResult, setCalcResult] = useState<CalcCarbonResponse | null>(null);
    const [loadingSessionDetail, setLoadingSessionDetail] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);

    useEffect(() => {
        if (!activeSessionId) {
            setActiveSession(null);
            return;
        }
        void loadSessionDetail(activeSessionId);
    }, [activeSessionId]);

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
        <div className="chat-workbench chat-workbench--single-column">
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
                        先输入本期的用电、天然气和柴油数据，系统会先给出总排放结论，再展开明细和因子来源。计算结果会关联到当前会话，但不会直接塞进问答消息流。
                    </Typography.Paragraph>
                    <div className="chat-session-state">
                        <Tag color="blue">当前会话：{activeSession ? "已关联" : "未关联"}</Tag>
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
                            <Typography.Text type="secondary">用于区分不同月份、季度或年度，不填也可以先算。</Typography.Text>
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>购电量（kWh）</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.electricity_kwh}
                                onChange={(value) => setFormState((current) => ({ ...current, electricity_kwh: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                            <Typography.Text type="secondary">示例：一间中小工厂或办公区一个月的总购电量。</Typography.Text>
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>天然气用量（m³）</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.natural_gas_m3}
                                onChange={(value) => setFormState((current) => ({ ...current, natural_gas_m3: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                            <Typography.Text type="secondary">示例：锅炉、供热或生产设备的天然气使用量。</Typography.Text>
                        </div>
                        <div className="calc-form-grid__item">
                            <Typography.Text strong>柴油用量（L）</Typography.Text>
                            <InputNumber
                                min={0}
                                value={formState.diesel_l}
                                onChange={(value) => setFormState((current) => ({ ...current, diesel_l: Number(value ?? 0) }))}
                                style={{ width: "100%" }}
                            />
                            <Typography.Text type="secondary">示例：柴油车辆、叉车或备用发电机的燃料消耗。</Typography.Text>
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
                            当前结果将{activeSessionId ? "关联到选中的会话" : "不关联任何会话"}
                        </Typography.Text>
                    </Space>
                </Card>

                <Card
                    className="calc-workbench__result-card"
                    title="核算结果"
                    extra={calcResult ? <Tag color="green">追踪号：{calcResult.trace_id}</Tag> : null}
                >
                    {loadingSessionDetail && !calcResult ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : calcResult ? (
                        <div className="calc-result-stack">
                            <div className="calc-result-summary">
                                <div className="calc-result-summary__headline">
                                    <Statistic
                                        title="本次总排放量"
                                        value={calcResult.total_emission_kgco2e}
                                        precision={3}
                                        suffix="kgCO2e"
                                    />
                                    <Typography.Paragraph type="secondary" className="calc-result-summary__hint">
                                        先看总量，再按来源查看分项和因子依据。
                                    </Typography.Paragraph>
                                </div>
                                <Space size={12} wrap>
                                    <Tag color={activeSessionId ? "blue" : "default"}>
                                        {activeSessionId ? `已关联到 ${activeSession?.title ?? activeSessionId}` : "未关联会话"}
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

                            <Collapse
                                ghost
                                defaultActiveKey={["breakdown"]}
                                items={[
                                    {
                                        key: "breakdown",
                                        label: "查看分项明细",
                                        children: (
                                            <List
                                                dataSource={calcResult.breakdown}
                                                renderItem={(item) => (
                                                    <List.Item key={item.item}>
                                                        <div className="calc-breakdown-row">
                                                            <div>
                                                                <Typography.Text strong>
                                                                    {itemLabelMap[item.item as keyof typeof itemLabelMap] ?? item.item}
                                                                </Typography.Text>
                                                                <Typography.Paragraph type="secondary" className="calc-breakdown-row__meta">
                                                                    {item.activity_value} {item.activity_unit} × {item.factor_value} {item.factor_unit}
                                                                </Typography.Paragraph>
                                                            </div>
                                                            <Tag color="green">{item.emission_kgco2e} kgCO2e</Tag>
                                                        </div>
                                                    </List.Item>
                                                )}
                                            />
                                        ),
                                    },
                                    {
                                        key: "citations",
                                        label: `查看因子依据（${calcResult.citations.length}）`,
                                        children: calcResult.citations.length ? (
                                            <List
                                                dataSource={calcResult.citations}
                                                renderItem={(citation) => (
                                                    <List.Item key={citation.factor_id}>
                                                        <div className="chat-citation-card">
                                                            <Space size={8} wrap>
                                                                <Typography.Text strong>{citation.factor_id}</Typography.Text>
                                                                <Tag color="gold">排放因子</Tag>
                                                            </Space>
                                                            <Typography.Paragraph className="chat-citation-card__snippet">
                                                                {citation.source}
                                                            </Typography.Paragraph>
                                                            {citation.source_url ? (
                                                                <Typography.Link href={citation.source_url} target="_blank" rel="noreferrer">
                                                                    <FileTextOutlined /> 查看来源
                                                                </Typography.Link>
                                                            ) : null}
                                                        </div>
                                                    </List.Item>
                                                )}
                                            />
                                        ) : (
                                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前没有可展示的因子来源。" />
                                        ),
                                    },
                                ]}
                            />
                        </div>
                    ) : (
                        <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description="提交活动数据后，这里会先显示总排放结论，再展开明细和因子来源。"
                        />
                    )}
                </Card>
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
