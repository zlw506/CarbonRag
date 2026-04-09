import { FileAddOutlined, ReloadOutlined, RocketOutlined, SoundOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Descriptions,
    Empty,
    List,
    Space,
    Spin,
    Statistic,
    Table,
    Tabs,
    Tag,
    Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { loadMyKnowledgeWorkspace } from "../../services/knowledge";
import type { KnowledgeItem, MyKnowledgeFeedback, MyKnowledgeReport, MyKnowledgeWorkspace } from "../../types/knowledge";
import { useNavigate } from "react-router-dom";

const emptyWorkspace: MyKnowledgeWorkspace = {
    uploads: [],
    knowledgeItems: [],
    reports: [],
    feedback: [],
    taskSummary: [],
};

export function MyKnowledgePage() {
    const navigate = useNavigate();
    const [workspace, setWorkspace] = useState<MyKnowledgeWorkspace>(emptyWorkspace);
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);

    useEffect(() => {
        void refreshWorkspace();
    }, []);

    const uploadColumns = useMemo<ColumnsType<KnowledgeItem>>(
        () => [
            { title: "文件名", dataIndex: "title", key: "title" },
            {
                title: "所属会话",
                key: "session",
                render: (_, record) => record.session_title ?? record.session_id ?? "未知会话",
            },
            {
                title: "处理状态",
                key: "status",
                render: (_, record) => (
                    <Tag color={statusColorMap[record.index_status]}>
                        {knowledgeStatusLabelMap[record.index_status] ?? record.index_status}
                    </Tag>
                ),
            },
            { title: "类型", dataIndex: "mime_type", key: "mime_type", render: (value) => value ?? "未知" },
            {
                title: "上传时间",
                key: "uploaded_at",
                render: (_, record) => formatTimestamp(record.uploaded_at ?? record.updated_at ?? ""),
            },
        ],
        [],
    );

    const knowledgeColumns = useMemo<ColumnsType<KnowledgeItem>>(
        () => [
            {
                title: "知识条目",
                key: "title",
                render: (_, record) => (
                    <Descriptions column={1} size="small">
                        <Descriptions.Item label="标题">{record.title}</Descriptions.Item>
                        <Descriptions.Item label="来源">{record.source_label}</Descriptions.Item>
                    </Descriptions>
                ),
            },
            {
                title: "层级",
                key: "scope",
                render: (_, record) => (
                    <Tag color={record.library_scope === "shared" ? "blue" : "green"}>
                        {record.library_scope === "shared" ? "共享知识" : "个人知识"}
                    </Tag>
                ),
            },
            {
                title: "来源类型",
                key: "source_type",
                render: (_, record) => <Tag>{knowledgeSourceLabelMap[record.source_type]}</Tag>,
            },
            {
                title: "解析 / 入库 / 索引",
                key: "pipeline",
                render: (_, record) => (
                    <Space size={6} wrap>
                        <Tag color={statusColorMap[record.parse_status]}>
                            解析 {knowledgeStatusLabelMap[record.parse_status] ?? record.parse_status}
                        </Tag>
                        <Tag color={statusColorMap[record.ingest_status]}>
                            入库 {knowledgeStatusLabelMap[record.ingest_status] ?? record.ingest_status}
                        </Tag>
                        <Tag color={statusColorMap[record.index_status]}>
                            索引 {knowledgeStatusLabelMap[record.index_status] ?? record.index_status}
                        </Tag>
                    </Space>
                ),
            },
            {
                title: "可挂接",
                key: "attachable",
                render: (_, record) => (
                    <Tag color={record.session_attachable ? "green" : "default"}>
                        {record.session_attachable ? "允许" : "不允许"}
                    </Tag>
                ),
            },
            {
                title: "更新时间",
                key: "updated_at",
                render: (_, record) => formatTimestamp(record.updated_at ?? ""),
            },
        ],
        [],
    );

    const reportColumns = useMemo<ColumnsType<MyKnowledgeReport>>(
        () => [
            { title: "报告标题", dataIndex: "title", key: "title" },
            {
                title: "所属会话",
                key: "session",
                render: (_, record) => record.session_title,
            },
            {
                title: "类型",
                key: "report_type",
                render: (_, record) => <Tag>{reportTypeLabelMap[record.report_type]}</Tag>,
            },
            {
                title: "更新时间",
                key: "updated_at",
                render: (_, record) => formatTimestamp(record.updated_at),
            },
            {
                title: "操作",
                key: "action",
                render: () => (
                    <Button size="small" onClick={() => navigate("/report")}>
                        打开报告页
                    </Button>
                ),
            },
        ],
        [navigate],
    );

    const feedbackColumns = useMemo<ColumnsType<MyKnowledgeFeedback>>(
        () => [
            { title: "反馈编号", dataIndex: "feedback_id", key: "feedback_id" },
            {
                title: "目标类型",
                key: "target_type",
                render: (_, record) => <Tag>{feedbackTargetLabelMap[record.target_type] ?? record.target_type}</Tag>,
            },
            {
                title: "评价",
                key: "rating",
                render: (_, record) => (
                    <Tag color={record.rating === "up" ? "green" : "red"}>
                        {record.rating === "up" ? "正向" : "负向"}
                    </Tag>
                ),
            },
            {
                title: "会话",
                key: "session_id",
                render: (_, record) => record.session_id ?? "未关联",
            },
            {
                title: "时间",
                key: "created_at",
                render: (_, record) => formatTimestamp(record.created_at),
            },
        ],
        [],
    );

    async function refreshWorkspace() {
        setLoading(true);
        setErrorMessage(null);
        try {
            const nextWorkspace = await loadMyKnowledgeWorkspace();
            setWorkspace(nextWorkspace);
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "当前无法加载我的知识库，请确认后端已启动。");
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="knowledge-workbench">
            <div className="knowledge-workbench__sidebar">
                <Card
                    title="我的知识概览"
                    extra={<Button icon={<ReloadOutlined />} onClick={() => void refreshWorkspace()} loading={loading}>刷新</Button>}
                >
                    <Typography.Paragraph type="secondary">
                        这里汇总你自己上传的文件、可挂接的知识条目、报告和反馈。当前版本先兼容现有会话数据，后续会直接对接知识条目主表。
                    </Typography.Paragraph>
                    <div className="admin-stats">
                        <Statistic title="上传" value={workspace.uploads.length} />
                        <Statistic title="知识条目" value={workspace.knowledgeItems.length} />
                        <Statistic title="报告" value={workspace.reports.length} />
                    </div>
                    <div style={{ height: 12 }} />
                    <Statistic title="反馈" value={workspace.feedback.length} />
                </Card>

                <Card title="最近任务">
                    <List
                        size="small"
                        dataSource={workspace.taskSummary.slice(0, 5)}
                        locale={{ emptyText: "暂无任务记录。" }}
                        renderItem={(item) => (
                            <List.Item>
                                <Space direction="vertical" size={4} style={{ width: "100%" }}>
                                    <Space size={8} wrap>
                                        <Tag color={taskStatusColorMap[item.status]}>{taskStatusLabelMap[item.status]}</Tag>
                                        <Tag>{item.scope}</Tag>
                                    </Space>
                                    <Typography.Text>{item.summary ?? "暂无摘要。"}</Typography.Text>
                                    <Typography.Text type="secondary">{formatTimestamp(item.created_at)}</Typography.Text>
                                </Space>
                            </List.Item>
                        )}
                    />
                </Card>
            </div>

            <div className="knowledge-workbench__main">
                {errorMessage ? (
                    <Alert
                        type="warning"
                        showIcon
                        className="chat-workbench__alert"
                        message="我的知识库提示"
                        description={errorMessage}
                    />
                ) : null}

                <Card
                    title="我的知识库"
                    extra={<Tag color="blue">当前登录用户可见</Tag>}
                    className="knowledge-workbench__content-card"
                >
                    {loading ? (
                        <div className="chat-workbench__loading">
                            <Spin size="large" />
                        </div>
                    ) : (
                        <Tabs
                            defaultActiveKey="uploads"
                            items={[
                                {
                                    key: "uploads",
                                    label: "我的上传",
                                    children: (
                                        <Table
                                            rowKey="knowledge_item_id"
                                            dataSource={workspace.uploads}
                                            columns={uploadColumns}
                                            pagination={false}
                                            size="small"
                                            locale={{ emptyText: <Empty description="暂无上传文件。" /> }}
                                        />
                                    ),
                                },
                                {
                                    key: "items",
                                    label: "我的知识条目",
                                    children: (
                                        <Table
                                            rowKey="knowledge_item_id"
                                            dataSource={workspace.knowledgeItems}
                                            columns={knowledgeColumns}
                                            pagination={false}
                                            size="small"
                                            locale={{ emptyText: <Empty description="当前没有可展示的知识条目。" /> }}
                                        />
                                    ),
                                },
                                {
                                    key: "reports",
                                    label: "我的报告",
                                    children: (
                                        <Table
                                            rowKey="report_id"
                                            dataSource={workspace.reports}
                                            columns={reportColumns}
                                            pagination={false}
                                            size="small"
                                            locale={{ emptyText: <Empty description="暂无报告。" /> }}
                                        />
                                    ),
                                },
                                {
                                    key: "feedback",
                                    label: "我的反馈",
                                    children: (
                                        <Table
                                            rowKey="feedback_id"
                                            dataSource={workspace.feedback}
                                            columns={feedbackColumns}
                                            pagination={false}
                                            size="small"
                                            locale={{
                                                emptyText: (
                                                    <Empty description="当前版本尚未暴露个人反馈列表，后续会接入我的反馈视图。" />
                                                ),
                                            }}
                                        />
                                    ),
                                },
                            ]}
                        />
                    )}
                </Card>
            </div>

            <div className="knowledge-workbench__panel">
                <SystemInfoPanel />
                <Card title="页面说明">
                    <Space direction="vertical" size={8}>
                        <Typography.Paragraph>
                            V1.1.0 把知识库视图拆成“我的上传、我的样例、我的报告、我的反馈”四个标签页，便于后续接入个人知识库与管理员共享知识库。
                        </Typography.Paragraph>
                        <Button type="primary" icon={<FileAddOutlined />} onClick={() => navigate("/")}>
                            返回问答工作台
                        </Button>
                        <Button icon={<RocketOutlined />} onClick={() => navigate("/carbon-calc")}>
                            查看碳核算
                        </Button>
                        <Button icon={<SoundOutlined />} onClick={() => navigate("/report")}>
                            查看报告页
                        </Button>
                    </Space>
                </Card>
            </div>
        </div>
    );
}

const knowledgeStatusLabelMap: Record<"pending" | "running" | "succeeded" | "failed" | "ready", string> = {
    pending: "待处理",
    running: "处理中",
    succeeded: "已完成",
    failed: "失败",
    ready: "已就绪",
};

const statusColorMap: Record<"pending" | "running" | "succeeded" | "failed" | "ready", string> = {
    pending: "default",
    running: "processing",
    succeeded: "green",
    failed: "red",
    ready: "blue",
};

const knowledgeSourceLabelMap: Record<string, string> = {
    uploaded_file: "上传文件",
    private_sample_repo: "共享知识条目",
    knowledge_item: "知识条目",
};

const reportTypeLabelMap: Record<string, string> = {
    policy_summary: "政策解读摘要",
    mixed_analysis: "政策 + 样例分析",
    carbon_summary: "碳核算结果说明",
};

const feedbackTargetLabelMap: Record<string, string> = {
    ask: "问答反馈",
    calc_carbon: "核算反馈",
    report: "报告反馈",
};

const taskStatusLabelMap: Record<string, string> = {
    queued: "排队中",
    running: "运行中",
    succeeded: "已完成",
    failed: "失败",
};

const taskStatusColorMap: Record<string, string> = {
    queued: "default",
    running: "processing",
    succeeded: "green",
    failed: "red",
};

function formatTimestamp(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value || "暂无";
    }
    return date.toLocaleString("zh-CN", {
        hour12: false,
        year: "numeric",
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
