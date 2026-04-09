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
                title: "User",
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
                title: "Role",
                key: "role",
                render: (_, record) => (
                    <Select
                        size="small"
                        value={record.role}
                        style={{ width: 120 }}
                        options={[
                            { label: "user", value: "user" },
                            { label: "admin", value: "admin" },
                        ]}
                        onChange={(value) => void handleUpdateUser(record, value as "user" | "admin", record.is_active)}
                    />
                ),
            },
            {
                title: "Active",
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
                title: "Usage",
                key: "counts",
                render: (_, record) => (
                    <Space size={8} wrap>
                        <Tag>{record.session_count} sessions</Tag>
                        <Tag>{record.report_count} reports</Tag>
                        <Tag>{record.feedback_count} feedback</Tag>
                    </Space>
                ),
            },
            {
                title: "Actions",
                key: "actions",
                render: (_, record) => (
                    <Space size={8} wrap>
                        {record.password_must_change ? <Tag color="orange">must change password</Tag> : null}
                        <Button
                            size="small"
                            disabled={userSavingId === record.user_id}
                            onClick={() => void handleResetPassword(record.user_id)}
                        >
                            Reset Password
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
            setErrorMessage(extractDetailMessage(error) ?? "Failed to load admin workspace.");
        } finally {
            setLoading(false);
        }
    }

    async function handleUpdateUser(
        record: AdminUserSummary,
        role: "user" | "admin",
        isActive: boolean,
    ) {
        setUserSavingId(record.user_id);
        setErrorMessage(null);
        try {
            const updated = await updateAdminUser(record.user_id, {
                role,
                is_active: isActive,
            });
            setUsers((current) => current.map((item) => (item.user_id === updated.user_id ? updated : item)));
            message.success(`Updated ${updated.username}.`);
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Failed to update user.");
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
                title: "Temporary Password",
                content: (
                    <Space direction="vertical" size={8}>
                        <Typography.Paragraph>
                            The password has been reset. The user must change it at next login.
                        </Typography.Paragraph>
                        <Typography.Text code>{result.temporary_password}</Typography.Text>
                    </Space>
                ),
            });
            await refreshUsers();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Failed to reset password.");
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
            message.success(`Updated ${updated.doc_id}.`);
            void refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Failed to update private sample.");
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
            message.success(`Knowledge refresh completed: ${task.status}.`);
            await refreshSystemStatus();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Knowledge refresh failed.");
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
                <Typography.Title level={2}>Admin Console</Typography.Title>
                <Typography.Paragraph>
                    V1.0.0 adds minimum governance for enterprise trial use: local identity, user-level data
                    isolation, system status visibility, private sample entry management, and manual knowledge refresh.
                </Typography.Paragraph>
                <Space size={12} wrap>
                    <Button icon={<ReloadOutlined />} onClick={() => void loadAdminWorkspace()} disabled={loading}>
                        Refresh
                    </Button>
                    <Select
                        value={knowledgeScope}
                        onChange={(value) => setKnowledgeScope(value)}
                        style={{ width: 180 }}
                        options={[
                            { label: "All sources", value: "all" },
                            { label: "Public policy only", value: "public_policy" },
                            { label: "Private sample only", value: "private_sample" },
                        ]}
                    />
                    <Button
                        type="primary"
                        icon={<SyncOutlined />}
                        loading={refreshingKnowledge}
                        onClick={() => void handleTriggerKnowledgeRefresh()}
                    >
                        Trigger Knowledge Refresh
                    </Button>
                </Space>
                {errorMessage ? (
                    <Alert
                        showIcon
                        type="warning"
                        message="Admin Workspace Warning"
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
                    <Card title="System Connection Status">
                        {systemStatus ? (
                            <Descriptions column={1} size="small" bordered>
                                <Descriptions.Item label="App">{systemStatus.app_name}</Descriptions.Item>
                                <Descriptions.Item label="Version">{systemStatus.version}</Descriptions.Item>
                                <Descriptions.Item label="Environment">{systemStatus.env}</Descriptions.Item>
                                <Descriptions.Item label="Database">{systemStatus.database_backend}</Descriptions.Item>
                                <Descriptions.Item label="Model">{systemStatus.model_name}</Descriptions.Item>
                                <Descriptions.Item label="Provider Mode">{systemStatus.model_provider_mode}</Descriptions.Item>
                                <Descriptions.Item label="Users">{systemStatus.total_users}</Descriptions.Item>
                                <Descriptions.Item label="Sessions">{systemStatus.total_sessions}</Descriptions.Item>
                                <Descriptions.Item label="Reports">{systemStatus.total_reports}</Descriptions.Item>
                                <Descriptions.Item label="Feedback">{systemStatus.total_feedback_entries}</Descriptions.Item>
                                <Descriptions.Item label="Private Samples">
                                    {systemStatus.enabled_private_samples} / {systemStatus.total_private_samples}
                                </Descriptions.Item>
                                <Descriptions.Item label="Latest Refresh">
                                    {systemStatus.latest_refresh_status ?? "none"}
                                </Descriptions.Item>
                            </Descriptions>
                        ) : (
                            <Typography.Text type="secondary">No system status available.</Typography.Text>
                        )}
                    </Card>

                    <Card title="Feedback Overview">
                        {feedbackOverview ? (
                            <Space direction="vertical" size={16} style={{ width: "100%" }}>
                                <div className="admin-stats">
                                    <Statistic title="Total" value={feedbackOverview.total_count} />
                                    <Statistic title="Ask Up" value={feedbackOverview.ask_up_count} />
                                    <Statistic title="Ask Down" value={feedbackOverview.ask_down_count} />
                                    <Statistic title="Calc Up" value={feedbackOverview.calc_up_count} />
                                    <Statistic title="Calc Down" value={feedbackOverview.calc_down_count} />
                                </div>
                                <List
                                    size="small"
                                    dataSource={feedbackOverview.recent_entries}
                                    locale={{ emptyText: "No feedback yet." }}
                                    renderItem={(item) => (
                                        <List.Item>
                                            <Space direction="vertical" size={2} style={{ width: "100%" }}>
                                                <Space size={8} wrap>
                                                    <Tag>{item.target_type}</Tag>
                                                    <Tag color={item.rating === "up" ? "green" : "red"}>{item.rating}</Tag>
                                                    <Typography.Text type="secondary">{item.owner_user_id}</Typography.Text>
                                                </Space>
                                                <Typography.Text type="secondary">{formatTimestamp(item.created_at)}</Typography.Text>
                                            </Space>
                                        </List.Item>
                                    )}
                                />
                            </Space>
                        ) : (
                            <Typography.Text type="secondary">No feedback summary available.</Typography.Text>
                        )}
                    </Card>

                    <Card title="Knowledge Tasks Overview">
                        <List
                            size="small"
                            dataSource={knowledgeTasks}
                            locale={{ emptyText: "No refresh task history." }}
                            renderItem={(item) => (
                                <List.Item>
                                    <Space direction="vertical" size={2} style={{ width: "100%" }}>
                                        <Space size={8} wrap>
                                            <Tag>{item.scope}</Tag>
                                            <Tag color={taskStatusColorMap[item.status]}>{item.status}</Tag>
                                        </Space>
                                        <Typography.Text>{item.summary ?? "No summary."}</Typography.Text>
                                        <Typography.Text type="secondary">{formatTimestamp(item.created_at)}</Typography.Text>
                                    </Space>
                                </List.Item>
                            )}
                        />
                    </Card>

                    <Card title="Private Sample Entry Management">
                        <List
                            size="small"
                            dataSource={privateSamples}
                            locale={{ emptyText: "No private samples available." }}
                            renderItem={(item) => (
                                <List.Item>
                                    <div className="admin-private-sample-row">
                                        <Space direction="vertical" size={4} style={{ width: "100%" }}>
                                            <Typography.Text strong>{item.title}</Typography.Text>
                                            <Space size={8} wrap>
                                                <Tag color="magenta">{item.sample_type}</Tag>
                                                <Tag>{item.business_topic}</Tag>
                                                <Tag>{item.doc_id}</Tag>
                                            </Space>
                                        </Space>
                                        <Space size={12} wrap>
                                            <Space size={6}>
                                                <Typography.Text type="secondary">Enabled</Typography.Text>
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
                                                <Typography.Text type="secondary">Attachable</Typography.Text>
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

                    <Card title="User Management">
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
