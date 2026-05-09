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
    List,
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
    searchCarbonFactors,
} from "../../services/carbonFactors";
import type {
    CarbonFactorCategoryNode,
    CarbonFactorDetail,
    CarbonFactorFacets,
    CarbonFactorSummary,
} from "../../types/carbonFactor";

const hotKeywords = ["电力", "柴油", "塑料", "交通", "建筑", "天然气"];

export function CarbonFactorsPage() {
    const [keyword, setKeyword] = useState("");
    const [category, setCategory] = useState<string | undefined>();
    const [industry, setIndustry] = useState<string | undefined>();
    const [year, setYear] = useState<number | undefined>();
    const [facets, setFacets] = useState<CarbonFactorFacets | null>(null);
    const [items, setItems] = useState<CarbonFactorSummary[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [detailLoading, setDetailLoading] = useState(false);
    const [selectedFactor, setSelectedFactor] = useState<CarbonFactorDetail | null>(null);
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
    }, [category, industry, year]);

    async function loadInitialData() {
        setLoading(true);
        setError(null);
        try {
            const nextFacets = await getCarbonFactorFacets();
            setFacets(nextFacets);
            const result = await searchCarbonFactors({ page_size: 24 });
            setItems(result.items);
            setTotal(result.total);
        } catch {
            setError("当前无法加载碳因子库，请稍后重试。");
        } finally {
            setLoading(false);
        }
    }

    async function runSearch(nextKeyword = keyword) {
        setLoading(true);
        setError(null);
        try {
            const result = await searchCarbonFactors({
                q: nextKeyword.trim() || undefined,
                category,
                industry,
                year,
                page_size: 24,
            });
            setItems(result.items);
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
    }

    return (
        <div className="carbon-factor-page">
            <section className="carbon-factor-hero">
                <div>
                    <Tag color="green">CarbonStop CCDB 公开数据对齐</Tag>
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
                            onSearch={(value) => void runSearch(value)}
                        />
                        <Space wrap size={8}>
                            <Typography.Text type="secondary">热门搜索：</Typography.Text>
                            {hotKeywords.map((item) => (
                                <Tag
                                    key={item}
                                    className="carbon-factor-hot-tag"
                                    onClick={() => {
                                        setKeyword(item);
                                        void runSearch(item);
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
                                onClick={() => {
                                    setIndustry(undefined);
                                    setCategory(undefined);
                                }}
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
                                    {typeof node.count === "number" ? `（${node.count}）` : ""}
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
                                onChange={setCategory}
                                options={(selectedGroup?.children ?? []).map((child) => ({
                                    label: child.count > 0
                                        ? `${child.label}（${child.count}）`
                                        : `${child.label}（暂无可计算公开值）`,
                                    value: child.label,
                                    disabled: child.count <= 0,
                                }))}
                            />
                            <Select
                                allowClear
                                value={year}
                                placeholder="发布年份"
                                style={{ minWidth: 140 }}
                                onChange={setYear}
                                options={(facets?.years ?? []).map((item) => ({ label: String(item), value: item }))}
                            />
                            <Button icon={<ReloadOutlined />} onClick={() => void loadInitialData()}>
                                刷新
                            </Button>
                            <Typography.Text type="secondary">
                                共 {total} 条可计算公开因子；加密展示值不会被硬编进计算库。
                            </Typography.Text>
                        </Space>
                    </Card>

                    {error ? <Card><Typography.Text type="danger">{error}</Typography.Text></Card> : null}

                    <Spin spinning={loading}>
                        {items.length ? (
                            <List
                                grid={{ gutter: 16, xs: 1, sm: 1, md: 2, xl: 3 }}
                                dataSource={items}
                                renderItem={(item) => (
                                    <List.Item key={item.factor_id}>
                                        <CarbonFactorCard item={item} onOpen={() => void openDetail(item.factor_id)} />
                                    </List.Item>
                                )}
                            />
                        ) : (
                            <Card>
                                <Empty description="没有匹配的公开因子" />
                            </Card>
                        )}
                    </Spin>
                </div>
            </section>

            <Drawer
                title={selectedFactor?.name ?? "因子详情"}
                open={Boolean(selectedFactor) || detailLoading}
                width={620}
                onClose={() => setSelectedFactor(null)}
            >
                {detailLoading ? <Spin /> : selectedFactor ? <CarbonFactorDetailView factor={selectedFactor} /> : null}
            </Drawer>
        </div>
    );
}

function CarbonFactorCard({ item, onOpen }: { item: CarbonFactorSummary; onOpen: () => void }) {
    return (
        <Card className="carbon-factor-card" onClick={onOpen}>
            <Space direction="vertical" size={10} style={{ width: "100%" }}>
                <Space size={8} wrap>
                    <Tag color="green">公开</Tag>
                    <Tag color="blue">{item.category}</Tag>
                    {item.industry ? <Tag>{item.industry}</Tag> : null}
                </Space>
                <Typography.Title level={4}>{item.name}</Typography.Title>
                <div className="carbon-factor-card__value">
                    {formatNumber(item.factor_value)}
                    <span>{item.factor_unit}</span>
                </div>
                <Space direction="vertical" size={2}>
                    <Typography.Text type="secondary">因子来源：{item.source?.publisher ?? "未知机构"}</Typography.Text>
                    <Typography.Text type="secondary">发布年份：{item.year ?? "未知"}</Typography.Text>
                </Space>
            </Space>
        </Card>
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
