import { ReloadOutlined, SyncOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Descriptions,
    List,
    Modal,
    Select,
    Space,
    Spin,
    Statistic,
    Switch,
    Table,
    Tag,
    Typography,
    message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";
import {
    getAdminFeedbackOverview,
    getAdminSystemStatus,
    listAdminPrivateSamples,
    listAdminUsers,
    listKnowledgeRefreshTasks,
    resetAdminUserPassword,
    triggerKnowledgeRefresh,
    updateAdminPrivateSample,
    updateAdminUser,
} from "../../services/admin";
import type {
    AdminFeedbackOverview,
    AdminPrivateSampleItem,
    AdminSystemStatus,
    AdminUserSummary,
    KnowledgeRefreshScope,
    KnowledgeRefreshTask,
} from "../../types/admin";

export function AdminPlaceholderPage() {
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [systemStatus, setSystemStatus] = useState<AdminSystemStatus | null>(null);
    const [users, setUsers] = useState<AdminUserSummary[]>([]);
    const [feedbackOverview, setFeedbackOverview] = useState<AdminFeedbackOverview | null>(null);
    const [privateSamples, setPrivateSamples] = useState<AdminPrivateSampleItem[]>([]);
    const [knowledgeTasks, setKnowledgeTasks] = useState<KnowledgeRefreshTask[]>([]);
    const [knowledgeScope, setKnowledgeScope] = useState<KnowledgeRefreshScope>("all");
    const [userSavingId, setUserSavingId] = useState<string | null>(null);
    const [privateSampleSavingId, setPrivateSampleSavingId] = useState<string | null>(null);
    const [refreshingKnowledge, setRefreshingKnowledge] = useState(false);

    const userColumns = useMemo<ColumnsType<AdminUserSummary>>(
        () => [
            {
                title: "用户",
                dataIndex: "username",
                key: "username",
                render: (_, record) => (
                    <Space direction="vertical" size={0}>
                        <Typography.Text strong>{record.username}</Typography.Text>
                        <Typography.Text type="secondary">{record.user_id}</Typography.Text>
                    </Space>
                ),
            },
            {
                title: "角色",
                key: "role",
                render: (_, record) => (
                    <Select
                        size="small"
                        value={record.role}
                        style={{ width: 120 }}
                        options={[
                            { label: "普通用户", value: "user" },
                            { label: "管理员", value: "admin" },
                        ]}
                        onChange={(value) => void handleUpdateUser(record, value as "user" | "admin", record.is_active)}
                    />
                ),
            },
            {
                title: "状态",
                key: "is_active",
                render: (_, record) => (
                    <Switch
                        size="small"
                        checked={record.is_active}
                        loading={userSavingId === record.user_id}
                        onChange={(checked) => void handleUpdateUser(record, record.role, checked)}
                    />
                ),
            },
            {
                title: "使用情况",
                key: "counts",
                render: (_, record) => (
                    <Space size={8} wrap>
                        <Tag>{record.session_count} 个会话</Tag>
                        <Tag>{record.report_count} 份报告</Tag>
                        <Tag>{record.feedback_count} 条反馈</Tag>
                    </Space>
                ),
            },
            {
                title: "操作",
                key: "actions",
                render: (_, record) => (
                    <Space size={8} wrap>
                        {record.password_must_change ? <Tag color="orange">下次登录需改密</Tag> : null}
                        <Button
                            size="small"
                            disabled={userSavingId === record.user_id}
                            onClick={() => void handleResetPassword(record.user_id)}
                        >
                            重置密码
                        </Button>
                    </Space>
                ),
            },
        ],
        [userSavingId, users],
    );

    useEffect(() => {
        void loadAdminWorkspace();
    }, []);

    async function loadAdminWorkspace() {
        setLoading(true);
        setErrorMessage(null);
        try {
            const [nextUsers, nextFeedback, nextPrivateSamples, nextTasks, nextStatus] = await Promise.all([
                listAdminUsers(),
                getAdminFeedbackOverview(),
                listAdminPrivateSamples(),
                listKnowledgeRefreshTasks(),
                getAdminSystemStatus(),
            ]);
            setUsers(nextUsers);
            setFeedbackOverview(nextFeedback);
            setPrivateSamples(nextPrivateSamples);
            setKnowledgeTasks(nextTasks);
            setSystemStatus(nextStatus);
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "加载管理员工作台失败。");
        } finally {
            setLoading(false);
        }
    }

    async function handleUpdateUser(record: AdminUserSummary, role: "user" | "admin", isActive: boolean) {
        setUserSavingId(record.user_id);
        setErrorMessage(null);
        try {
            const updated = await updateAdminUser(record.user_id, {
                role,
                is_active: isActive,
            });
            setUsers((current) => current.map((item) => (item.user_id === updated.user_id ? updated : item)));
            message.success(`已更新用户「${updated.username}」。`);
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "更新用户失败。");
        } finally {
            setUserSavingId(null);
        }
    }

    async function handleResetPassword(userId: string) {
        setUserSavingId(userId);
        setErrorMessage(null);
        try {
            const result = await resetAdminUserPassword(userId);
            Modal.info({
                title: "临时密码",
                content: (
                    <Space direction="vertical" size={8}>
                        <Typography.Paragraph>密码已重置。该用户下次登录时必须修改密码。</Typography.Paragraph>
                        <Typography.Text code>{result.temporary_password}</Typography.Text>
                    </Space>
                ),
            });
            await refreshUsers();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "重置密码失败。");
        } finally {
            setUserSavingId(null);
        }
    }

    async function handleUpdatePrivateSample(
        record: AdminPrivateSampleItem,
        patch: Partial<Pick<AdminPrivateSampleItem, "is_enabled" | "session_attachable">>,
    ) {
        setPrivateSampleSavingId(record.doc_id);
        setErrorMessage(null);
        try {
            const updated = await updateAdminPrivateSample(record.doc_id, {
                is_enabled: patch.is_enabled ?? record.is_enabled,
                session_attachable: patch.session_attachable ?? record.session_attachable,
            });
            setPrivateSamples((current) => current.map((item) => (item.doc_id === updated.doc_id ? updated : item)));
            message.success(`已更新样例「${updated.doc_id}」。`);
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "更新企业样例失败。");
        } finally {
            setPrivateSampleSavingId(null);
        }
    }

    async function handleTriggerKnowledgeRefresh() {
        setRefreshingKnowledge(true);
        setErrorMessage(null);
        try {
            const task = await triggerKnowledgeRefresh({ scope: knowledgeScope });
            setKnowledgeTasks((current) => [task, ...current.filter((item) => item.task_id !== task.task_id)]);
            message.success(`知识刷新已完成：${taskStatusLabelMap[task.status] ?? task.status}。`);
            await refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "知识刷新失败。");
        } finally {
            setRefreshingKnowledge(false);
        }
    }

    async function refreshUsers() {
        const nextUsers = await listAdminUsers();
        setUsers(nextUsers);
        await refreshSystemStatus();
    }

    async function refreshSystemStatus() {
        const nextStatus = await getAdminSystemStatus();
        setSystemStatus(nextStatus);
    }

    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Card>
                <Typography.Title level={2}>管理员控制台</Typography.Title>
                <Typography.Paragraph>
                    V1.0.0 增加了企业试用版所需的最小治理能力：本地身份、按用户隔离数据、系统状态查看、企业样例入口管理，以及手动知识刷新。
                </Typography.Paragraph>
                <Space size={12} wrap>
                    <Button icon={<ReloadOutlined />} onClick={() => void loadAdminWorkspace()} disabled={loading}>
                        刷新
                    </Button>
                    <Select
                        value={knowledgeScope}
                        onChange={(value) => setKnowledgeScope(value)}
                        style={{ width: 180 }}
                        options={[
                            { label: "全部来源", value: "all" },
                            { label: "仅公共政策", value: "public_policy" },
                            { label: "仅企业样例", value: "private_sample" },
                        ]}
                    />
                    <Button
                        type="primary"
                        icon={<SyncOutlined />}
                        loading={refreshingKnowledge}
                        onClick={() => void handleTriggerKnowledgeRefresh()}
                    >
                        触发知识刷新
                    </Button>
                </Space>
                {errorMessage ? (
                    <Alert
                        showIcon
                        type="warning"
                        message="管理员工作台提示"
                        description={errorMessage}
                        className="auth-card__alert"
                    />
                ) : null}
            </Card>

            {loading ? (
                <Card>
                    <div className="chat-workbench__loading">
                        <Spin size="large" />
                    </div>
                </Card>
            ) : (
                <div className="admin-grid">
                    <Card title="系统连接状态">
                        {systemStatus ? (
                            <Descriptions column={1} size="small" bordered>
                                <Descriptions.Item label="应用名称">{systemStatus.app_name}</Descriptions.Item>
                                <Descriptions.Item label="版本">{systemStatus.version}</Descriptions.Item>
                                <Descriptions.Item label="环境">{resolveLabel(environmentLabelMap, systemStatus.env)}</Descriptions.Item>
                                <Descriptions.Item label="数据库">
                                    {resolveLabel(databaseBackendLabelMap, systemStatus.database_backend)}
                                </Descriptions.Item>
                                <Descriptions.Item label="模型">{systemStatus.model_name}</Descriptions.Item>
                                <Descriptions.Item label="模型服务模式">
                                    {resolveLabel(providerModeLabelMap, systemStatus.model_provider_mode)}
                                </Descriptions.Item>
                                <Descriptions.Item label="用户数">{systemStatus.total_users}</Descriptions.Item>
                                <Descriptions.Item label="会话数">{systemStatus.total_sessions}</Descriptions.Item>
                                <Descriptions.Item label="报告数">{systemStatus.total_reports}</Descriptions.Item>
                                <Descriptions.Item label="反馈数">{systemStatus.total_feedback_entries}</Descriptions.Item>
                                <Descriptions.Item label="企业样例">
                                    {systemStatus.enabled_private_samples} / {systemStatus.total_private_samples}
                                </Descriptions.Item>
                                <Descriptions.Item label="最近刷新">
                                    {systemStatus.latest_refresh_status
                                        ? resolveLabel(taskStatusLabelMap, systemStatus.latest_refresh_status)
                                        : "暂无"}
                                </Descriptions.Item>
                            </Descriptions>
                        ) : (
                            <Typography.Text type="secondary">暂无系统状态。</Typography.Text>
                        )}
                    </Card>

                    <Card title="反馈概览">
                        {feedbackOverview ? (
                            <Space direction="vertical" size={16} style={{ width: "100%" }}>
                                <div className="admin-stats">
                                    <Statistic title="总数" value={feedbackOverview.total_count} />
                                    <Statistic title="问答赞成" value={feedbackOverview.ask_up_count} />
                                    <Statistic title="问答反对" value={feedbackOverview.ask_down_count} />
                                    <Statistic title="核算赞成" value={feedbackOverview.calc_up_count} />
                                    <Statistic title="核算反对" value={feedbackOverview.calc_down_count} />
                                </div>
                                <List
                                    size="small"
                                    dataSource={feedbackOverview.recent_entries}
                                    locale={{ emptyText: "暂无反馈。" }}
                                    renderItem={(item) => (
                                        <List.Item>
                                            <Space direction="vertical" size={2} style={{ width: "100%" }}>
                                                <Space size={8} wrap>
                                                    <Tag>{resolveLabel(feedbackTargetLabelMap, item.target_type)}</Tag>
                                                    <Tag color={item.rating === "up" ? "green" : "red"}>
                                                        {resolveLabel(feedbackRatingLabelMap, item.rating)}
                                                    </Tag>
                                                    <Typography.Text type="secondary">{item.owner_user_id}</Typography.Text>
                                                </Space>
                                                <Typography.Text type="secondary">{formatTimestamp(item.created_at)}</Typography.Text>
                                            </Space>
                                        </List.Item>
                                    )}
                                />
                            </Space>
                        ) : (
                            <Typography.Text type="secondary">暂无反馈汇总。</Typography.Text>
                        )}
                    </Card>

                    <Card title="知识任务概览">
                        <List
                            size="small"
                            dataSource={knowledgeTasks}
                            locale={{ emptyText: "暂无刷新任务历史。" }}
                            renderItem={(item) => (
                                <List.Item>
                                    <Space direction="vertical" size={2} style={{ width: "100%" }}>
                                        <Space size={8} wrap>
                                            <Tag>{resolveLabel(knowledgeScopeLabelMap, item.scope)}</Tag>
                                            <Tag color={taskStatusColorMap[item.status]}>
                                                {resolveLabel(taskStatusLabelMap, item.status)}
                                            </Tag>
                                        </Space>
                                        <Typography.Text>{item.summary ?? "暂无摘要。"}</Typography.Text>
                                        <Typography.Text type="secondary">{formatTimestamp(item.created_at)}</Typography.Text>
                                    </Space>
                                </List.Item>
                            )}
                        />
                    </Card>

                    <Card title="企业样例入口管理">
                        <List
                            size="small"
                            dataSource={privateSamples}
                            locale={{ emptyText: "暂无可用企业样例。" }}
                            renderItem={(item) => (
                                <List.Item>
                                    <div className="admin-private-sample-row">
                                        <Space direction="vertical" size={4} style={{ width: "100%" }}>
                                            <Typography.Text strong>{item.title}</Typography.Text>
                                            <Space size={8} wrap>
                                                <Tag color="magenta">{resolveLabel(sampleTypeLabelMap, item.sample_type)}</Tag>
                                                <Tag>{resolveLabel(businessTopicLabelMap, item.business_topic)}</Tag>
                                                <Tag>{item.doc_id}</Tag>
                                            </Space>
                                        </Space>
                                        <Space size={12} wrap>
                                            <Space size={6}>
                                                <Typography.Text type="secondary">启用</Typography.Text>
                                                <Switch
                                                    size="small"
                                                    checked={item.is_enabled}
                                                    loading={privateSampleSavingId === item.doc_id}
                                                    onChange={(checked) =>
                                                        void handleUpdatePrivateSample(item, { is_enabled: checked })
                                                    }
                                                />
                                            </Space>
                                            <Space size={6}>
                                                <Typography.Text type="secondary">可挂接</Typography.Text>
                                                <Switch
                                                    size="small"
                                                    checked={item.session_attachable}
                                                    loading={privateSampleSavingId === item.doc_id}
                                                    onChange={(checked) =>
                                                        void handleUpdatePrivateSample(item, { session_attachable: checked })
                                                    }
                                                />
                                            </Space>
                                        </Space>
                                    </div>
                                </List.Item>
                            )}
                        />
                    </Card>

                    <Card title="用户管理">
                        <Table
                            rowKey="user_id"
                            columns={userColumns}
                            dataSource={users}
                            pagination={false}
                            size="small"
                        />
                    </Card>
                </div>
            )}
        </Space>
    );
}

const taskStatusColorMap = {
    running: "processing",
    succeeded: "green",
    failed: "red",
} as const;

const taskStatusLabelMap = {
    running: "运行中",
    succeeded: "已完成",
    failed: "失败",
} as const;

const knowledgeScopeLabelMap = {
    all: "全部来源",
    public_policy: "仅公共政策",
    private_sample: "仅企业样例",
} as const;

const feedbackRatingLabelMap = {
    up: "正向",
    down: "负向",
} as const;

const feedbackTargetLabelMap = {
    ask: "问答反馈",
    calc_carbon: "核算反馈",
} as const;

const sampleTypeLabelMap = {
    doc: "文档",
    table: "表格",
} as const;

const businessTopicLabelMap = {
    energy: "能耗",
    production: "生产",
    logistics: "物流",
    project_background: "项目背景",
} as const;

const environmentLabelMap = {
    development: "本地开发环境",
    production: "生产环境",
    staging: "预发布环境",
} as const;

const databaseBackendLabelMap = {
    sqlite: "本地数据库",
    postgresql: "生产数据库",
} as const;

const providerModeLabelMap = {
    openai_compatible: "兼容模式",
    stub: "模拟模式",
} as const;

function formatTimestamp(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
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

function resolveLabel<T extends Record<string, string>>(map: T, value: string) {
    return map[value as keyof T] ?? value;
}
