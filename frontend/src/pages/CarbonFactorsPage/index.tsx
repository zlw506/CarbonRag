import {
    DatabaseOutlined,
    FilterOutlined,
    ReloadOutlined,
    SearchOutlined,
} from "@ant-design/icons";
import {
    Button,
    Card,
    Descriptions,
    Drawer,
    Empty,
    Input,
    Pagination,
    Segmented,
    Select,
    Space,
    Spin,
    Tag,
    Typography,
} from "antd";
import { useEffect, useMemo, useState } from "react";
import {
    getCarbonFactor,
    getCarbonFactorFacets,
    searchCarbonFactorCatalog,
    searchCarbonFactors,
} from "../../services/carbonFactors";
import type {
    CarbonFactorCatalogEntry,
    CarbonFactorCategoryNode,
    CarbonFactorDetail,
    CarbonFactorFacets,
    CarbonFactorSummary,
} from "../../types/carbonFactor";

const hotKeywords = ["电力", "柴油", "塑料", "交通", "建筑", "天然气"];
const PAGE_SIZE = 8;

export function CarbonFactorsPage() {
    const [keyword, setKeyword] = useState("");
    const [category, setCategory] = useState<string | undefined>();
    const [industry, setIndustry] = useState<string | undefined>();
    const [year, setYear] = useState<number | undefined>();
    const [facets, setFacets] = useState<CarbonFactorFacets | null>(null);
    const [items, setItems] = useState<CarbonFactorSummary[]>([]);
    const [catalogItems, setCatalogItems] = useState<CarbonFactorCatalogEntry[]>([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [viewMode, setViewMode] = useState<"catalog" | "calculation">("catalog");
    const [loading, setLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [selectedFactor, setSelectedFactor] = useState<CarbonFactorDetail | null>(null);
    const [selectedCatalogEntry, setSelectedCatalogEntry] = useState<CarbonFactorCatalogEntry | null>(null);
    const [error, setError] = useState<string | null>(null);

    const selectedGroup = useMemo(
        () => facets?.category_tree.find((node) => node.label === industry),
        [facets?.category_tree, industry],
    );

    useEffect(() => {
        void loadInitialData();
    }, []);

    useEffect(() => {
        void runSearch();
    }, [category, industry, year, page, viewMode]);

    async function loadInitialData() {
        setLoading(true);
        setError(null);
        try {
            const nextFacets = await getCarbonFactorFacets();
            setFacets(nextFacets);
            const result = await searchCarbonFactorCatalog({ page_size: PAGE_SIZE });
            setCatalogItems(result.items);
            setItems([]);
            setTotal(result.total);
        } catch {
            setError("当前无法加载碳因子库，请稍后重试。");
        } finally {
            setLoading(false);
        }
    }

    async function runSearch(nextKeyword = keyword, nextPage = page) {
        setLoading(true);
        setError(null);
        try {
            if (viewMode === "catalog") {
                const result = await searchCarbonFactorCatalog({
                    q: nextKeyword.trim() || undefined,
                    category,
                    industry,
                    year,
                    page: nextPage,
                    page_size: PAGE_SIZE,
                });
                setCatalogItems(result.items);
                setItems([]);
                setTotal(result.total);
                return;
            }
            const result = await searchCarbonFactors({
                q: nextKeyword.trim() || undefined,
                category,
                industry,
                year,
                page: nextPage,
                page_size: PAGE_SIZE,
            });
            setItems(result.items);
            setCatalogItems([]);
            setTotal(result.total);
        } catch {
            setError("搜索失败，请检查网络或稍后重试。");
        } finally {
            setLoading(false);
        }
    }

    async function openDetail(factorId: string) {
        setDetailLoading(true);
        try {
            setSelectedFactor(await getCarbonFactor(factorId));
        } finally {
            setDetailLoading(false);
        }
    }

    function selectIndustry(node: CarbonFactorCategoryNode) {
        setIndustry(node.label);
        setCategory(undefined);
        setPage(1);
    }

    function resetFilters() {
        setIndustry(undefined);
        setCategory(undefined);
        setPage(1);
    }

    function selectedChildCount(child: { count: number; raw_count?: number }) {
        return viewMode === "catalog" ? (child.raw_count ?? child.count) : child.count;
    }

    function selectedGroupCount(node: CarbonFactorCategoryNode) {
        return viewMode === "catalog"
            ? node.children.reduce((sum, child) => sum + selectedChildCount(child), 0)
            : (node.count ?? 0);
    }

    return (
        <div className="carbon-factor-page">
            <section className="carbon-factor-hero">
                <div>
                    <Typography.Text className="admin-console__eyebrow">碳核算 · 因子数据</Typography.Text>
                    <Typography.Title level={2}>碳因子库</Typography.Title>
                    <Typography.Paragraph type="secondary">
                        整合 CarbonStop CCDB 公开展示的分类、因子、机构和来源字段，后端可检索、可维护，并可供后续碳核算优先调用。
                    </Typography.Paragraph>
                </div>
                <Card className="carbon-factor-hero__search">
                    <Space direction="vertical" size={12} style={{ width: "100%" }}>
                        <Input.Search
                            size="large"
                            allowClear
                            value={keyword}
                            enterButton="搜索"
                            prefix={<SearchOutlined />}
                            placeholder="搜索电力、柴油、交通、塑料、建筑材料…"
                            onChange={(event) => setKeyword(event.target.value)}
                            onSearch={(value) => {
                                setPage(1);
                                void runSearch(value, 1);
                            }}
                        />
                        <Space wrap size={8}>
                            <Typography.Text type="secondary">热门搜索：</Typography.Text>
                            {hotKeywords.map((item) => (
                                <Tag
                                    key={item}
                                    className="carbon-factor-hot-tag"
                                    onClick={() => {
                                        setKeyword(item);
                                        setPage(1);
                                        void runSearch(item, 1);
                                    }}
                                >
                                    {item}
                                </Tag>
                            ))}
                        </Space>
                    </Space>
                </Card>
            </section>

            <section className="carbon-factor-layout">
                <Card
                    title={
                        <Space>
                            <FilterOutlined />
                            分类
                        </Space>
                    }
                    className="carbon-factor-category-card"
                >
                    {facets?.category_tree.length ? (
                        <Space direction="vertical" size={10} style={{ width: "100%" }}>
                            <Button
                                block
                                type={!industry ? "primary" : "default"}
                                onClick={resetFilters}
                            >
                                全部分类
                            </Button>
                            {facets.category_tree.map((node) => (
                                <Button
                                    key={node.label}
                                    block
                                    type={industry === node.label ? "primary" : "default"}
                                    onClick={() => selectIndustry(node)}
                                >
                                    {node.label}
                                    {`（${selectedGroupCount(node)}）`}
                                </Button>
                            ))}
                        </Space>
                    ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无分类数据" />
                    )}
                </Card>

                <div className="carbon-factor-main">
                    <Card className="carbon-factor-filter-card">
                        <Space size={12} wrap>
                            <Select
                                allowClear
                                value={category}
                                placeholder="二级分类"
                                style={{ minWidth: 180 }}
                                disabled={!selectedGroup}
                                onChange={(value) => {
                                    setCategory(value);
                                    setPage(1);
                                }}
                                options={(selectedGroup?.children ?? []).map((child) => ({
                                    label: `${child.label}（${selectedChildCount(child)}）`,
                                    value: child.label,
                                    disabled: selectedChildCount(child) <= 0,
                                }))}
                            />
                            <Select
                                allowClear
                                value={year}
                                placeholder="发布年份"
                                style={{ minWidth: 140 }}
                                onChange={(value) => {
                                    setYear(value);
                                    setPage(1);
                                }}
                                options={(facets?.years ?? []).map((item) => ({ label: String(item), value: item }))}
                            />
                            <Segmented
                                value={viewMode}
                                onChange={(value) => {
                                    setViewMode(value as "catalog" | "calculation");
                                    setPage(1);
                                }}
                                options={[
                                    { label: "全部公开目录", value: "catalog" },
                                    { label: "仅可计算因子", value: "calculation" },
                                ]}
                            />
                            <Button icon={<ReloadOutlined />} onClick={() => void loadInitialData()}>
                                刷新
                            </Button>
                            <Typography.Text type="secondary">
                                {viewMode === "catalog"
                                    ? `共 ${total} 条公开目录项；未公开数值仅展示目录，不进入计算库。`
                                    : `共 ${total} 条可计算公开因子；加密展示值不会被硬编进计算库。`}
                            </Typography.Text>
                        </Space>
                    </Card>

                    {error ? <Card><Typography.Text type="danger">{error}</Typography.Text></Card> : null}

                    <Spin spinning={loading}>
                        {(viewMode === "catalog" ? catalogItems.length : items.length) ? (
                            <Card className="carbon-factor-results-panel">
                                <div className="carbon-factor-results-grid">
                                    {viewMode === "catalog"
                                        ? catalogItems.map((item) => (
                                            <CarbonFactorCatalogCard
                                                key={item.entry_id}
                                                item={item}
                                                onOpen={() => setSelectedCatalogEntry(item)}
                                            />
                                        ))
                                        : items.map((item) => (
                                            <CarbonFactorCard
                                                key={item.factor_id}
                                                item={item}
                                                onOpen={() => void openDetail(item.factor_id)}
                                            />
                                        ))}
                                </div>
                                <div className="carbon-factor-results-footer">
                                    <Pagination
                                        size="small"
                                        current={page}
                                        pageSize={PAGE_SIZE}
                                        total={total}
                                        showSizeChanger={false}
                                        onChange={setPage}
                                    />
                                </div>
                            </Card>
                        ) : (
                            <Card>
                                <Empty description={viewMode === "catalog" ? "没有匹配的公开目录项" : "没有匹配的可计算公开因子"} />
                            </Card>
                        )}
                    </Spin>
                </div>
            </section>

            <Drawer
                title={selectedFactor?.name ?? selectedCatalogEntry?.name ?? "因子详情"}
                open={Boolean(selectedFactor) || Boolean(selectedCatalogEntry) || detailLoading}
                width={620}
                onClose={() => {
                    setSelectedFactor(null);
                    setSelectedCatalogEntry(null);
                }}
            >
                {detailLoading ? <Spin /> : selectedFactor ? <CarbonFactorDetailView factor={selectedFactor} /> : null}
                {!detailLoading && selectedCatalogEntry ? <CarbonFactorCatalogDetailView entry={selectedCatalogEntry} /> : null}
            </Drawer>
        </div>
    );
}

function CarbonFactorCatalogCard({ item, onOpen }: { item: CarbonFactorCatalogEntry; onOpen: () => void }) {
    return (
        <Card className="carbon-factor-card carbon-factor-card--compact" onClick={onOpen}>
            <div className="carbon-factor-card__content">
                <Typography.Title level={5} className="carbon-factor-card__title" title={item.name}>
                    {item.name}
                </Typography.Title>
                <div className="carbon-factor-card__value carbon-factor-card__value--small">
                    {item.is_calculation_ready && typeof item.factor_value === "number" ? formatNumber(item.factor_value) : "未公开数值"}
                    <span>{item.factor_unit ?? "官网加密展示"}</span>
                </div>
                <Typography.Text type="secondary" className="carbon-factor-card__meta" title={item.publisher ?? "未知机构"}>
                    来源：{item.publisher ?? "未知机构"}
                </Typography.Text>
            </div>
        </Card>
    );
}

function CarbonFactorCard({ item, onOpen }: { item: CarbonFactorSummary; onOpen: () => void }) {
    return (
        <Card className="carbon-factor-card carbon-factor-card--compact" onClick={onOpen}>
            <div className="carbon-factor-card__content">
                <Typography.Title level={5} className="carbon-factor-card__title" title={item.name}>
                    {item.name}
                </Typography.Title>
                <div className="carbon-factor-card__value carbon-factor-card__value--small">
                    {formatNumber(item.factor_value)}
                    <span>{item.factor_unit}</span>
                </div>
                <Typography.Text type="secondary" className="carbon-factor-card__meta" title={item.source?.publisher ?? "未知机构"}>
                    来源：{item.source?.publisher ?? "未知机构"}
                </Typography.Text>
            </div>
        </Card>
    );
}

function CarbonFactorCatalogDetailView({ entry }: { entry: CarbonFactorCatalogEntry }) {
    const raw = entry.metadata?.raw_row as Record<string, unknown> | undefined;
    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <div className="carbon-factor-detail-value">
                <Typography.Text type="secondary">公开目录状态</Typography.Text>
                <Typography.Title level={3}>
                    {entry.is_calculation_ready ? "可直接用于核算" : "官网公开目录，数值加密展示"}
                </Typography.Title>
                <Typography.Paragraph type="secondary">
                    {entry.is_calculation_ready
                        ? "该条目含公开数值，已经进入 CarbonRag 可计算因子库。"
                        : "该条目来自 CarbonStop CCDB 公开目录，但官网未公开可计算数值，因此只展示目录与来源，不参与自动核算。"}
                </Typography.Paragraph>
            </div>
            <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="名称">{entry.name}</Descriptions.Item>
                <Descriptions.Item label="分类">{entry.industry ? `${entry.industry} / ${entry.category}` : entry.category}</Descriptions.Item>
                <Descriptions.Item label="公开展示值">{entry.raw_value ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="单位">{entry.factor_unit ?? "未公开"}</Descriptions.Item>
                <Descriptions.Item label="地区">{entry.region ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="年份">{entry.year ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="来源机构">{entry.publisher ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="原始来源">{entry.source_title ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="来源平台">
                    <Typography.Link href={entry.source_url ?? "https://www.carbonstop.com/ccdb"} target="_blank">
                        CarbonStop CCDB 中国碳数据库
                    </Typography.Link>
                </Descriptions.Item>
                <Descriptions.Item label="规格">{String(raw?.specification ?? "未标注")}</Descriptions.Item>
                <Descriptions.Item label="说明">{String(raw?.description ?? "无")}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="原始字段快照">
                <Typography.Paragraph copyable className="carbon-factor-raw-json">
                    {JSON.stringify(raw ?? entry.metadata, null, 2)}
                </Typography.Paragraph>
            </Card>
        </Space>
    );
}

function CarbonFactorDetailView({ factor }: { factor: CarbonFactorDetail }) {
    const raw = factor.metadata?.raw_row as Record<string, unknown> | undefined;
    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <div className="carbon-factor-detail-value">
                <Typography.Text type="secondary">公开因子值</Typography.Text>
                <Typography.Title level={2}>
                    {formatNumber(factor.factor_value)} <small>{factor.factor_unit}</small>
                </Typography.Title>
            </div>
            <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="分类">{factor.industry ? `${factor.industry} / ${factor.category}` : factor.category}</Descriptions.Item>
                <Descriptions.Item label="适用范围">{factor.scope}</Descriptions.Item>
                <Descriptions.Item label="地区">{factor.region_name ?? factor.region ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="年份">{factor.year ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="活动单位">{factor.activity_unit}</Descriptions.Item>
                <Descriptions.Item label="结果单位">{factor.co2e_unit}</Descriptions.Item>
                <Descriptions.Item label="来源机构">{factor.source?.publisher ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="原始来源">{factor.source?.title ?? "未标注"}</Descriptions.Item>
                <Descriptions.Item label="来源平台">
                    <Typography.Link href={factor.source?.source_url ?? "https://www.carbonstop.com/ccdb"} target="_blank">
                        CarbonStop CCDB 中国碳数据库
                    </Typography.Link>
                </Descriptions.Item>
                <Descriptions.Item label="规格">{String(raw?.specification ?? "未标注")}</Descriptions.Item>
                <Descriptions.Item label="说明">{String(raw?.description ?? factor.metadata?.notes ?? "无")}</Descriptions.Item>
            </Descriptions>
            <Card size="small" title="原始字段快照">
                <Typography.Paragraph copyable className="carbon-factor-raw-json">
                    {JSON.stringify(raw ?? factor.metadata, null, 2)}
                </Typography.Paragraph>
            </Card>
        </Space>
    );
}

function formatNumber(value: number) {
    if (!Number.isFinite(value)) {
        return "-";
    }
    if (Math.abs(value) >= 100) {
        return value.toFixed(2);
    }
    if (Math.abs(value) >= 1) {
        return value.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
    }
    return value.toPrecision(4).replace(/0+$/, "").replace(/\.$/, "");
}
