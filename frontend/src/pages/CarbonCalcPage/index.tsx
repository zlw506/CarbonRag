import {
    CloseOutlined,
    ExperimentOutlined,
    FileTextOutlined,
    ReloadOutlined,
} from "@ant-design/icons";
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
import { useEffect, useMemo, useState } from "react";
import { FeedbackButtonGroup } from "../../components/FeedbackButtonGroup";
import { useWorkbenchShellContext } from "../../layouts/WorkbenchShellContext";
import { submitCarbonCalculation } from "../../services/carbon";
import { searchCarbonFactors } from "../../services/carbonFactors";
import { getSession } from "../../services/sessions";
import type { CalcCarbonResponse, CarbonActivityInput } from "../../types/carbon";
import type { CarbonFactorSummary } from "../../types/carbonFactor";
import type { SessionDetail } from "../../types/session";

type CalculatorGroupKey = "clothes" | "food" | "home" | "travel" | "daily";

interface SelectedCalculatorItem {
    row_id: string;
    factor: CarbonFactorSummary;
    activity_value: number;
}

const CALCULATOR_GROUPS: Array<{ key: CalculatorGroupKey; label: string; hint: string }> = [
    { key: "clothes", label: "衣", hint: "纺织、服装、清洁用品等消费品因子" },
    { key: "food", label: "食", hint: "食品、烟酒茶、农林牧渔相关因子" },
    { key: "home", label: "住", hint: "电力、热力、燃气、建筑材料与居家能源" },
    { key: "travel", label: "行", hint: "陆上交通、公共交通、海上交通与物流运输" },
    { key: "daily", label: "用", hint: "日用品、电子设备、废弃物、快递物流等" },
];

const TREE_ABSORPTION_KGCO2E = 18.3;
const MAX_VISIBLE_OPTIONS_PER_GROUP = 36;

export function CarbonCalcPage() {
    const { activeSessionId, refreshSessions } = useWorkbenchShellContext();
    const [activeSession, setActiveSession] = useState<SessionDetail | null>(null);
    const [periodLabel, setPeriodLabel] = useState("");
    const [factors, setFactors] = useState<CarbonFactorSummary[]>([]);
    const [factorLoading, setFactorLoading] = useState(false);
    const [activeGroup, setActiveGroup] = useState<CalculatorGroupKey>("travel");
    const [factorSearch, setFactorSearch] = useState("");
    const [selectedItems, setSelectedItems] = useState<SelectedCalculatorItem[]>([]);
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

    useEffect(() => {
        void loadCalculatorFactors();
    }, []);

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

    async function loadCalculatorFactors() {
        setFactorLoading(true);
        setTransportError(null);
        try {
            const pageSize = 100;
            const firstPage = await searchCarbonFactors({ quality: "public_ccdb", page: 1, page_size: pageSize });
            const pages = Math.min(Math.ceil(firstPage.total / pageSize), 10);
            const rest = await Promise.all(
                Array.from({ length: Math.max(pages - 1, 0) }, (_, index) =>
                    searchCarbonFactors({ quality: "public_ccdb", page: index + 2, page_size: pageSize }),
                ),
            );
            const merged = [firstPage, ...rest].flatMap((page) => page.items);
            setFactors(dedupeFactors(merged));
        } catch {
            setFactors([]);
            setTransportError("当前无法读取本地碳因子库，碳计算器暂不可用。");
        } finally {
            setFactorLoading(false);
        }
    }

    const factorsByGroup = useMemo(() => {
        const grouped: Record<CalculatorGroupKey, CarbonFactorSummary[]> = {
            clothes: [],
            food: [],
            home: [],
            travel: [],
            daily: [],
        };
        factors.forEach((factor) => grouped[groupFactorForCalculator(factor)].push(factor));
        Object.keys(grouped).forEach((key) => {
            grouped[key as CalculatorGroupKey] = sortCalculatorFactors(grouped[key as CalculatorGroupKey]);
        });
        return grouped;
    }, [factors]);

    const visibleFactors = useMemo(() => {
        const keyword = factorSearch.trim().toLowerCase();
        const source = factorsByGroup[activeGroup];
        const filtered = keyword
            ? source.filter((factor) =>
                [
                    factor.name,
                    factor.category,
                    factor.industry ?? "",
                    factor.source?.publisher ?? "",
                    factor.source?.title ?? "",
                ]
                    .join(" ")
                    .toLowerCase()
                    .includes(keyword),
            )
            : source;
        return filtered.slice(0, MAX_VISIBLE_OPTIONS_PER_GROUP);
    }, [activeGroup, factorSearch, factorsByGroup]);

    const localTotalKgco2e = useMemo(
        () => roundCarbonValue(
            selectedItems.reduce(
                (sum, item) =>
                    sum
                    + item.activity_value
                    * item.factor.factor_value
                    * resultUnitToKgco2eMultiplier(item.factor.co2e_unit || item.factor.factor_unit),
                0,
            ),
        ),
        [selectedItems],
    );

    const treeCount = Math.ceil(localTotalKgco2e / TREE_ABSORPTION_KGCO2E);
    const positiveItems = selectedItems.filter((item) => item.activity_value > 0);

    function addFactor(factor: CarbonFactorSummary) {
        setSelectedItems((current) => {
            const existed = current.find((item) => item.factor.factor_id === factor.factor_id);
            if (existed) {
                return current.map((item) =>
                    item.factor.factor_id === factor.factor_id
                        ? { ...item, activity_value: item.activity_value + 1 }
                        : item,
                );
            }
            return [
                ...current,
                {
                    row_id: `${factor.factor_id}-${Date.now()}`,
                    factor,
                    activity_value: 1,
                },
            ];
        });
    }

    function updateSelectedValue(rowId: string, value: number | null) {
        setSelectedItems((current) =>
            current.map((item) =>
                item.row_id === rowId
                    ? { ...item, activity_value: Number(value ?? 0) }
                    : item,
            ),
        );
    }

    function removeSelected(rowId: string) {
        setSelectedItems((current) => current.filter((item) => item.row_id !== rowId));
    }

    async function handleSubmit() {
        if (!positiveItems.length) {
            setTransportError("请先选择至少一个排放源，并输入大于 0 的活动数据。");
            return;
        }
        setSubmitting(true);
        setTransportError(null);
        try {
            const response = await submitCarbonCalculation({
                session_id: activeSessionId ?? undefined,
                period_label: periodLabel.trim() || undefined,
                activity_items: positiveItems.map((item) => buildActivityInput(item.factor, item.activity_value)),
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
                    className="calc-workbench__form-card carbon-calculator-card"
                    title={
                        <div className="carbon-calculator-title">
                            <span>碳计算器</span>
                            <Tag color="green">使用本地碳因子库</Tag>
                        </div>
                    }
                    extra={<Tag color="blue">{activeSession?.title ?? "未选择会话"}</Tag>}
                >
                    <Typography.Paragraph type="secondary" className="carbon-calculator-intro">
                        选择需要计算的类目并输入活动数据。计算因子来自当前 CarbonRag 碳因子库，结果会保存到当前会话，供报告和后续问答引用。
                    </Typography.Paragraph>

                    <div className="chat-session-state carbon-calculator-meta">
                        <Tag color="blue">当前会话：{activeSession ? "已关联" : "未关联"}</Tag>
                        <Tag color="green">上传附件：{uploadedFileCount}</Tag>
                        <Tag color="magenta">挂接样例：{privateSampleCount}</Tag>
                        <Tag color="cyan">可用因子：{factors.length}</Tag>
                    </div>

                    <div className="carbon-calculator-toolbar">
                        <Input
                            value={periodLabel}
                            onChange={(event) => setPeriodLabel(event.target.value)}
                            placeholder="期间标签，例如：2026-Q1"
                            className="carbon-calculator-toolbar__period"
                        />
                        <Input.Search
                            value={factorSearch}
                            onChange={(event) => setFactorSearch(event.target.value)}
                            placeholder="在当前类目内搜索排放源"
                            allowClear
                            className="carbon-calculator-toolbar__search"
                        />
                        <Button icon={<ReloadOutlined />} onClick={() => void loadCalculatorFactors()} loading={factorLoading}>
                            刷新因子
                        </Button>
                    </div>

                    <div className="carbon-calculator-layout">
                        <section className="carbon-calculator-source-panel" aria-label="排放源类型">
                            <div className="carbon-calculator-source-panel__header">类型</div>
                            <div className="carbon-calculator-groups">
                                {CALCULATOR_GROUPS.map((group) => (
                                    <button
                                        key={group.key}
                                        type="button"
                                        className={`carbon-calculator-group ${activeGroup === group.key ? "carbon-calculator-group--active" : ""}`}
                                        onClick={() => setActiveGroup(group.key)}
                                    >
                                        <span className="carbon-calculator-group__label">{group.label}</span>
                                        <span className="carbon-calculator-group__count">{factorsByGroup[group.key].length}</span>
                                    </button>
                                ))}
                            </div>
                            <Typography.Paragraph className="carbon-calculator-group-hint">
                                {CALCULATOR_GROUPS.find((item) => item.key === activeGroup)?.hint}
                            </Typography.Paragraph>

                            <div className="carbon-calculator-options">
                                {factorLoading ? (
                                    <div className="carbon-calculator-loading"><Spin /></div>
                                ) : visibleFactors.length ? (
                                    visibleFactors.map((factor) => (
                                        <button
                                            key={factor.factor_id}
                                            type="button"
                                            className="carbon-calculator-option"
                                            onClick={() => addFactor(factor)}
                                            title={`${factor.name}：${factor.factor_value} ${factor.factor_unit}`}
                                        >
                                            <span className="carbon-calculator-option__name">{factor.name}</span>
                                            <span className="carbon-calculator-option__meta">
                                                {formatFactorValue(factor.factor_value)} {factor.factor_unit}
                                            </span>
                                        </button>
                                    ))
                                ) : (
                                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前类目暂无可计算因子。" />
                                )}
                            </div>
                        </section>

                        <section className="carbon-calculator-result-panel" aria-label="已选排放源">
                            <div className="carbon-calculator-result-panel__header">
                                <span>排放源</span>
                                <span>活动数据</span>
                            </div>
                            <div className="carbon-calculator-selected-list">
                                {selectedItems.length ? (
                                    selectedItems.map((item) => {
                                        const itemEmission = roundCarbonValue(
                                            item.activity_value
                                            * item.factor.factor_value
                                            * resultUnitToKgco2eMultiplier(item.factor.co2e_unit || item.factor.factor_unit),
                                        );
                                        return (
                                            <div className="carbon-calculator-selected" key={item.row_id}>
                                                <div className="carbon-calculator-selected__info">
                                                    <Typography.Text strong ellipsis title={item.factor.name}>
                                                        {item.factor.name}
                                                    </Typography.Text>
                                                    <Typography.Text type="secondary">
                                                        {formatFactorValue(item.factor.factor_value)} {item.factor.factor_unit}
                                                    </Typography.Text>
                                                    <Typography.Text type="secondary" ellipsis title={item.factor.source?.publisher ?? item.factor.source?.title ?? "未知来源"}>
                                                        来源：{item.factor.source?.publisher ?? item.factor.source?.title ?? "未知来源"}
                                                    </Typography.Text>
                                                </div>
                                                <div className="carbon-calculator-selected__input">
                                                    <InputNumber
                                                        min={0}
                                                        value={item.activity_value}
                                                        onChange={(value) => updateSelectedValue(item.row_id, Number(value ?? 0))}
                                                    />
                                                    <Typography.Text className="carbon-calculator-selected__unit">
                                                        {item.factor.activity_unit}
                                                    </Typography.Text>
                                                    <Typography.Text className="carbon-calculator-selected__emission">
                                                        {formatFactorValue(itemEmission)} kgCO₂e
                                                    </Typography.Text>
                                                    <Button
                                                        type="text"
                                                        size="small"
                                                        icon={<CloseOutlined />}
                                                        onClick={() => removeSelected(item.row_id)}
                                                        aria-label={`移除 ${item.factor.name}`}
                                                    />
                                                </div>
                                            </div>
                                        );
                                    })
                                ) : (
                                    <Empty
                                        image={Empty.PRESENTED_IMAGE_SIMPLE}
                                        description="从左侧选择排放源后，这里会生成可填写的计算项。"
                                    />
                                )}
                            </div>
                            <footer className="carbon-calculator-summary">
                                <div>
                                    <Typography.Text type="secondary">总排放量</Typography.Text>
                                    <div className="carbon-calculator-summary__total">
                                        {formatFactorValue(localTotalKgco2e)} kgCO₂e
                                    </div>
                                </div>
                                <Typography.Text type="secondary">
                                    约需种植 <b>{treeCount}</b> 棵树抵消这些碳排放
                                </Typography.Text>
                                <Button
                                    type="primary"
                                    icon={<ExperimentOutlined />}
                                    loading={submitting}
                                    disabled={!positiveItems.length}
                                    onClick={() => void handleSubmit()}
                                >
                                    保存本次核算
                                </Button>
                            </footer>
                        </section>
                    </div>
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
                                        suffix="kgCO₂e"
                                    />
                                    <Typography.Paragraph type="secondary" className="calc-result-summary__hint">
                                        结果已由后端因子引擎复核，并保存本次活动数据、因子快照和来源依据。
                                    </Typography.Paragraph>
                                </div>
                                <Space size={12} wrap>
                                    <Tag color="purple">因子快照：{calcResult.factor_snapshot.length}</Tag>
                                    <Tag color="cyan">换算 trace：{calcResult.unit_conversion_trace.length}</Tag>
                                    <Tag color="geekblue">公式 trace：{calcResult.formula_trace.length}</Tag>
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

                            {calcResult.warnings.length ? (
                                <Alert
                                    type="warning"
                                    showIcon
                                    message="核算口径提示"
                                    description={
                                        <ul className="calc-result-warning-list">
                                            {calcResult.warnings.map((warning) => (
                                                <li key={warning}>{warning}</li>
                                            ))}
                                        </ul>
                                    }
                                />
                            ) : null}

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
                                                    <List.Item key={`${item.factor_id}-${item.activity_name}`}>
                                                        <div className="calc-breakdown-row">
                                                            <div>
                                                                <Typography.Text strong>
                                                                    {item.activity_name ?? item.item}
                                                                </Typography.Text>
                                                                <Typography.Paragraph type="secondary" className="calc-breakdown-row__meta">
                                                                    {item.activity_value} {item.activity_unit} × {item.factor_value} {item.factor_unit}
                                                                </Typography.Paragraph>
                                                            </div>
                                                            <Tag color="green">{item.emission_kgco2e} kgCO₂e</Tag>
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
                                    {
                                        key: "factor_snapshot",
                                        label: `查看因子快照（${calcResult.factor_snapshot.length}）`,
                                        children: calcResult.factor_snapshot.length ? (
                                            <List
                                                dataSource={calcResult.factor_snapshot}
                                                renderItem={(factor) => (
                                                    <List.Item key={factor.factor_id}>
                                                        <div className="chat-citation-card">
                                                            <Space size={8} wrap>
                                                                <Typography.Text strong>{factor.activity_name}</Typography.Text>
                                                                <Tag color={factor.source_type === "official" ? "green" : "blue"}>
                                                                    {factor.source_type}
                                                                </Tag>
                                                                <Tag>{factor.scope}</Tag>
                                                                <Tag>{factor.activity_category}</Tag>
                                                            </Space>
                                                            <Typography.Paragraph className="chat-citation-card__snippet">
                                                                {factor.factor_value} {factor.factor_unit}，活动单位 {factor.activity_unit}
                                                                {factor.region_name || factor.region ? `，区域 ${factor.region_name ?? factor.region}` : ""}
                                                                {factor.year ? `，年份 ${factor.year}` : ""}
                                                            </Typography.Paragraph>
                                                            <Typography.Paragraph type="secondary">
                                                                来源：{factor.source_name}
                                                                {factor.notes ? `；备注：${factor.notes}` : ""}
                                                            </Typography.Paragraph>
                                                        </div>
                                                    </List.Item>
                                                )}
                                            />
                                        ) : (
                                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前没有因子快照。" />
                                        ),
                                    },
                                ]}
                            />
                        </div>
                    ) : (
                        <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description="选择排放源并保存核算后，这里会展示后端复核结果、分项和因子来源。"
                        />
                    )}
                </Card>
            </div>
        </div>
    );
}

function dedupeFactors(items: CarbonFactorSummary[]) {
    const map = new Map<string, CarbonFactorSummary>();
    items.forEach((item) => map.set(item.factor_id, item));
    return Array.from(map.values());
}

function sortCalculatorFactors(items: CarbonFactorSummary[]) {
    return [...items].sort((a, b) => {
        const aYear = a.year ?? 0;
        const bYear = b.year ?? 0;
        if (aYear !== bYear) {
            return bYear - aYear;
        }
        return a.name.localeCompare(b.name, "zh-CN");
    });
}

function groupFactorForCalculator(factor: CarbonFactorSummary): CalculatorGroupKey {
    const text = `${factor.name} ${factor.category} ${factor.industry ?? ""}`.toLowerCase();
    if (includesAny(text, ["交通", "运输", "汽车", "公交", "火车", "飞机", "轮船", "物流", "公里"])) {
        return "travel";
    }
    if (includesAny(text, ["食品", "烟酒", "茶", "农林牧渔", "肉", "米", "奶", "菜", "啤酒"])) {
        return "food";
    }
    if (includesAny(text, ["电力", "热力", "天然气", "煤气", "燃气", "建筑", "水泥", "玻璃", "供暖", "石油化工"])) {
        return "home";
    }
    if (includesAny(text, ["纺织", "服装", "织物", "衣", "洗衣"])) {
        return "clothes";
    }
    return "daily";
}

function includesAny(text: string, keywords: string[]) {
    return keywords.some((keyword) => text.includes(keyword.toLowerCase()));
}

function buildActivityInput(factor: CarbonFactorSummary, activityValue: number): CarbonActivityInput {
    return {
        scope: toCarbonScope(factor.scope),
        activity_category: factor.category,
        activity_name: factor.name,
        activity_value: activityValue,
        activity_unit: factor.activity_unit,
        region: factor.region ?? factor.region_code ?? null,
        year: factor.year ?? null,
        factor_preference: "official_latest",
        requested_factor_id: factor.factor_id,
        metadata: {
            factor_id: factor.factor_id,
            factor_unit: factor.factor_unit,
            source: factor.source?.publisher ?? factor.source?.title ?? "CarbonRag 碳因子库",
        },
    };
}

function toCarbonScope(value: string): "scope1" | "scope2" | "scope3" {
    return value === "scope1" || value === "scope2" || value === "scope3" ? value : "scope3";
}

function resultUnitToKgco2eMultiplier(unit: string) {
    const normalized = unit.replace("₂", "2").toLowerCase();
    const resultUnit = normalized.includes("/") ? normalized.split("/", 1)[0] : normalized;
    if (resultUnit.includes("tco2e")) {
        return 1000;
    }
    if (resultUnit.includes("gco2e")) {
        return 0.001;
    }
    return 1;
}

function roundCarbonValue(value: number) {
    return Math.round(value * 1_000_000) / 1_000_000;
}

function formatFactorValue(value: number) {
    if (!Number.isFinite(value)) {
        return "0";
    }
    if (Math.abs(value) >= 100) {
        return value.toFixed(2);
    }
    if (Math.abs(value) >= 1) {
        return value.toFixed(3).replace(/\.?0+$/, "");
    }
    return value.toPrecision(4).replace(/\.?0+$/, "");
}

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
