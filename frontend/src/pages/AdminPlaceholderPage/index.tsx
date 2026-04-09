import { ReloadOutlined, SyncOutlined } from "@ant-design/icons";
import {
    Alert,
    Button,
    Card,
    Descriptions,
    Empty,
    List,
    Modal,
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
    listAdminUsers,
    resetAdminUserPassword,
    updateAdminPrivateSample,
    updateAdminUser,
} from "../../services/admin";
import {
    listAdminKnowledgeItems,
    listAdminKnowledgeTasks,
    retryKnowledgeTask,
    triggerKnowledgeRebuild,
    triggerKnowledgeScan,
} from "../../services/knowledge";
import type { AdminFeedbackOverview, AdminSystemStatus, AdminUserSummary } from "../../types/admin";
import type { KnowledgeItem, KnowledgeTask } from "../../types/knowledge";

type KnowledgeTaskRefreshAction = "scan" | "rebuild" | null;

export function AdminPlaceholderPage() {
    const [loading, setLoading] = useState(true);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [systemStatus, setSystemStatus] = useState<AdminSystemStatus | null>(null);
    const [users, setUsers] = useState<AdminUserSummary[]>([]);
    const [feedbackOverview, setFeedbackOverview] = useState<AdminFeedbackOverview | null>(null);
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
    const [knowledgeTasks, setKnowledgeTasks] = useState<KnowledgeTask[]>([]);
    const [userSavingId, setUserSavingId] = useState<string | null>(null);
    const [knowledgeItemSavingId, setKnowledgeItemSavingId] = useState<string | null>(null);
    const [refreshingKnowledge, setRefreshingKnowledge] = useState<KnowledgeTaskRefreshAction>(null);

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
                    <Space direction="vertical" size={4}>
                        <Typography.Text>{roleLabelMap[record.role] ?? record.role}</Typography.Text>
                        <Button
                            size="small"
                            disabled={userSavingId === record.user_id}
                            onClick={() => void handleUpdateUser(record, record.role === "admin" ? "user" : "admin", record.is_active)}
                        >
                            切换角色
                        </Button>
                    </Space>
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
        [userSavingId],
    );

    const knowledgeColumns = useMemo<ColumnsType<KnowledgeItem>>(
        () => [
            {
                title: "知识条目",
                key: "title",
                render: (_, record) => (
                    <Space direction="vertical" size={2}>
                        <Typography.Text strong>{record.title}</Typography.Text>
                        <Typography.Text type="secondary">{record.source_label}</Typography.Text>
                        <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            {record.source_ref}
                        </Typography.Text>
                    </Space>
                ),
            },
            {
                title: "层级",
                key: "library_scope",
                render: (_, record) => (
                    <Tag color={record.library_scope === "shared" ? "blue" : "green"}>
                        {libraryScopeLabelMap[record.library_scope]}
                    </Tag>
                ),
            },
            {
                title: "来源类型",
                key: "source_type",
                render: (_, record) => <Tag>{sourceTypeLabelMap[record.source_type] ?? record.source_type}</Tag>,
            },
            {
                title: "解析 / 入库 / 索引",
                key: "pipeline",
                render: (_, record) => (
                    <Space size={6} wrap>
                        <Tag color={statusColorMap[record.parse_status]}>{statusLabelMap[record.parse_status]}</Tag>
                        <Tag color={statusColorMap[record.ingest_status]}>{statusLabelMap[record.ingest_status]}</Tag>
                        <Tag color={statusColorMap[record.index_status]}>{statusLabelMap[record.index_status]}</Tag>
                    </Space>
                ),
            },
            {
                title: "启用 / 可挂接",
                key: "switches",
                render: (_, record) => {
                    const editable = record.library_scope === "shared";
                    if (!editable) {
                        return <Tag color="default">个人知识只读</Tag>;
                    }
                    return (
                        <Space size={12} wrap>
                            <Space size={6}>
                                <Typography.Text type="secondary">启用</Typography.Text>
                                <Switch
                                    size="small"
                                    checked={record.is_enabled}
                                    loading={knowledgeItemSavingId === record.knowledge_item_id}
                                    onChange={(checked) =>
                                        void handleUpdateKnowledgeItem(record, {
                                            is_enabled: checked,
                                            session_attachable: record.session_attachable,
                                        })
                                    }
                                />
                            </Space>
                            <Space size={6}>
                                <Typography.Text type="secondary">可挂接</Typography.Text>
                                <Switch
                                    size="small"
                                    checked={record.session_attachable}
                                    loading={knowledgeItemSavingId === record.knowledge_item_id}
                                    onChange={(checked) =>
                                        void handleUpdateKnowledgeItem(record, {
                                            is_enabled: record.is_enabled,
                                            session_attachable: checked,
                                        })
                                    }
                                />
                            </Space>
                        </Space>
                    );
                },
            },
            {
                title: "更新时间",
                key: "updated_at",
                render: (_, record) => formatTimestamp(record.updated_at ?? ""),
            },
        ],
        [knowledgeItemSavingId],
    );

    const taskColumns = useMemo<ColumnsType<KnowledgeTask>>(
        () => [
            { title: "任务编号", dataIndex: "task_id", key: "task_id", width: 220 },
            {
                title: "动作",
                key: "task_type",
                render: (_, record) => <Tag>{taskTypeLabelMap[record.task_type] ?? record.task_type}</Tag>,
            },
            {
                title: "范围",
                key: "scope",
                render: (_, record) => <Tag>{taskScopeLabelMap[record.scope] ?? record.scope}</Tag>,
            },
            {
                title: "状态",
                key: "status",
                render: (_, record) => <Tag color={taskStatusColorMap[record.status]}>{taskStatusLabelMap[record.status]}</Tag>,
            },
            {
                title: "摘要",
                key: "summary",
                render: (_, record) => (
                    <Typography.Text type="secondary">{record.summary ?? "暂无摘要。"}</Typography.Text>
                ),
            },
            {
                title: "对象",
                key: "target_label",
                render: (_, record) => record.target_label ?? "全部",
            },
            {
                title: "时间",
                key: "created_at",
                render: (_, record) => formatTimestamp(record.created_at),
            },
            {
                title: "操作",
                key: "actions",
                render: (_, record) => (
                    <Button size="small" disabled={record.status === "running"} onClick={() => void handleRetryTask(record.task_id)}>
                        重试
                    </Button>
                ),
            },
        ],
        [],
    );

    useEffect(() => {
        void loadAdminWorkspace();
    }, []);

    async function loadAdminWorkspace() {
        setLoading(true);
        setErrorMessage(null);
        try {
            const [nextUsers, nextFeedback, nextKnowledgeItems, nextTasks, nextStatus] = await Promise.all([
                listAdminUsers(),
                getAdminFeedbackOverview(),
                listAdminKnowledgeItems(),
                listAdminKnowledgeTasks(),
                getAdminSystemStatus(),
            ]);
            setUsers(nextUsers);
            setFeedbackOverview(nextFeedback);
            setKnowledgeItems(nextKnowledgeItems);
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

    async function handleUpdateKnowledgeItem(
        record: KnowledgeItem,
        patch: Pick<KnowledgeItem, "is_enabled" | "session_attachable">,
    ) {
        setKnowledgeItemSavingId(record.knowledge_item_id);
        setErrorMessage(null);
        try {
            const updated = await updateAdminPrivateSample(record.knowledge_item_id, patch);
            setKnowledgeItems((current) =>
                current.map((item) =>
                    item.knowledge_item_id === record.knowledge_item_id
                        ? {
                              ...item,
                              is_enabled: updated.is_enabled,
                              session_attachable: updated.session_attachable,
                          }
                        : item,
                ),
            );
            message.success(`已更新知识条目「${record.title}」。`);
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "更新知识条目失败。");
        } finally {
            setKnowledgeItemSavingId(null);
        }
    }

    async function handleRetryTask(taskId: string) {
        setErrorMessage(null);
        try {
            const updated = await retryKnowledgeTask(taskId);
            setKnowledgeTasks((current) => [updated, ...current.filter((item) => item.task_id !== updated.task_id)]);
            message.success("任务重试已提交。");
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "重试任务失败。");
        }
    }

    async function handleTriggerKnowledgeRefresh(action: KnowledgeTaskRefreshAction) {
        setRefreshingKnowledge(action);
        setErrorMessage(null);
        try {
            const task = action === "rebuild" ? await triggerKnowledgeRebuild() : await triggerKnowledgeScan();
            setKnowledgeTasks((current) => [task, ...current.filter((item) => item.task_id !== task.task_id)]);
            message.success(`知识任务已提交：${taskTypeLabelMap[task.task_type] ?? task.task_type}。`);
            await loadAdminWorkspace();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "知识任务触发失败。");
        } finally {
            setRefreshingKnowledge(null);
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
                    这里汇总用户、知识条目、更新任务、反馈和系统状态。管理员可以在这里查看知识库条目、触发扫描与重建，并管理用户与反馈概览。
                </Typography.Paragraph>
                <Space size={12} wrap>
                    <Button icon={<ReloadOutlined />} onClick={() => void loadAdminWorkspace()} disabled={loading}>
                        刷新
                    </Button>
                    <Button
                        icon={<SyncOutlined />}
                        loading={refreshingKnowledge === "scan"}
                        onClick={() => void handleTriggerKnowledgeRefresh("scan")}
                    >
                        扫描知识变动
                    </Button>
                    <Button
                        type="primary"
                        icon={<SyncOutlined />}
                        loading={refreshingKnowledge === "rebuild"}
                        onClick={() => void handleTriggerKnowledgeRefresh("rebuild")}
                    >
                        重建知识索引
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
                                <Descriptions.Item label="环境">{environmentLabelMap[systemStatus.env] ?? systemStatus.env}</Descriptions.Item>
                                <Descriptions.Item label="数据库">
                                    {databaseBackendLabelMap[systemStatus.database_backend] ?? systemStatus.database_backend}
                                </Descriptions.Item>
                                <Descriptions.Item label="模型">{systemStatus.model_name}</Descriptions.Item>
                                <Descriptions.Item label="模型服务模式">
                                    {providerModeLabelMap[systemStatus.model_provider_mode] ?? systemStatus.model_provider_mode}
                                </Descriptions.Item>
                                <Descriptions.Item label="用户数">{systemStatus.total_users}</Descriptions.Item>
                                <Descriptions.Item label="会话数">{systemStatus.total_sessions}</Descriptions.Item>
                                <Descriptions.Item label="报告数">{systemStatus.total_reports}</Descriptions.Item>
                                <Descriptions.Item label="反馈数">{systemStatus.total_feedback_entries}</Descriptions.Item>
                                <Descriptions.Item label="知识条目">
                                    {systemStatus.enabled_private_samples} / {systemStatus.total_private_samples}
                                </Descriptions.Item>
                                <Descriptions.Item label="最近刷新">
                                    {systemStatus.latest_refresh_status
                                        ? taskStatusLabelMap[systemStatus.latest_refresh_status]
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
                                                    <Tag>{feedbackTargetLabelMap[item.target_type] ?? item.target_type}</Tag>
                                                    <Tag color={item.rating === "up" ? "green" : "red"}>
                                                        {item.rating === "up" ? "正向" : "负向"}
                                                    </Tag>
                                                    <Typography.Text type="secondary">{item.owner_user_id ?? "匿名"}</Typography.Text>
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

                    <Card
                        title="知识条目 / 文档列表"
                        extra={
                            <Tag color="blue">
                                {knowledgeItems.length} 个条目
                            </Tag>
                        }
                    >
                        <Table
                            rowKey="knowledge_item_id"
                            columns={knowledgeColumns}
                            dataSource={knowledgeItems}
                            pagination={{ pageSize: 6 }}
                            size="small"
                            locale={{ emptyText: <Empty description="暂无知识条目。" /> }}
                        />
                    </Card>

                    <Card title="更新任务列表">
                        <Table
                            rowKey="task_id"
                            columns={taskColumns}
                            dataSource={knowledgeTasks}
                            pagination={{ pageSize: 6 }}
                            size="small"
                            locale={{ emptyText: <Empty description="暂无知识任务。" /> }}
                        />
                    </Card>

                    <Card title="用户列表">
                        <Table rowKey="user_id" columns={userColumns} dataSource={users} pagination={false} size="small" />
                    </Card>
                </div>
            )}
        </Space>
    );
}

const statusLabelMap: Record<string, string> = {
    pending: "待处理",
    running: "处理中",
    succeeded: "已完成",
    failed: "失败",
    ready: "已就绪",
};

const statusColorMap: Record<string, string> = {
    pending: "default",
    running: "processing",
    succeeded: "green",
    failed: "red",
    ready: "blue",
};

const roleLabelMap = {
    user: "普通用户",
    admin: "管理员",
} as const;

const libraryScopeLabelMap = {
    personal: "个人知识",
    shared: "共享知识",
} as const;

const sourceTypeLabelMap: Record<string, string> = {
    uploaded_file: "上传文件",
    private_sample_repo: "共享知识条目",
    knowledge_item: "知识条目",
};

const taskTypeLabelMap: Record<string, string> = {
    upload_ingest: "上传入库",
    rebuild: "重建索引",
    rescan: "扫描变动",
    retry: "重试任务",
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

const taskScopeLabelMap: Record<string, string> = {
    public_policy: "公共政策",
    private_sample: "私有知识",
    all: "全部范围",
};

const feedbackTargetLabelMap: Record<string, string> = {
    ask: "问答反馈",
    calc_carbon: "核算反馈",
    report: "报告反馈",
};

const environmentLabelMap: Record<string, string> = {
    development: "本地开发环境",
    production: "生产环境",
    staging: "预发布环境",
};

const databaseBackendLabelMap: Record<string, string> = {
    sqlite: "本地数据库",
    postgresql: "生产数据库",
};

const providerModeLabelMap: Record<string, string> = {
    openai_compatible: "兼容模式",
    stub: "模拟模式",
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
