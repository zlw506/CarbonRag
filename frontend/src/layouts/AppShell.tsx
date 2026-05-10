import {
    DatabaseOutlined,
    DesktopOutlined,
    ExperimentOutlined,
    FolderOpenOutlined,
    FileTextOutlined,
    ClusterOutlined,
    LogoutOutlined,
    SearchOutlined,
    SettingOutlined,
} from "@ant-design/icons";
import { App as AntdApp, Avatar, Button, Input, Layout, Menu, Modal, Popover, Space, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { useSettings } from "../app/SettingsContext";
import { SessionRail, useResponsiveSessionRail } from "../components/SessionRail";
import { ADMIN_NAV_ITEM, getNavigationItems } from "../constants/navigation";
import { createSession, deleteSession, listSessions, updateSession } from "../services/sessions";
import type { SessionSummary } from "../types/session";
import type { WorkbenchShellContextValue } from "./WorkbenchShellContext";

const { Header, Content, Sider } = Layout;

const iconMap = {
    "/": <SearchOutlined />,
    "/my-knowledge": <FolderOpenOutlined />,
    "/kb": <DatabaseOutlined />,
    "/rag-lab": <ClusterOutlined />,
    "/carbon-factors": <DatabaseOutlined />,
    "/carbon-calc": <ExperimentOutlined />,
    "/report": <FileTextOutlined />,
    "/admin": <DesktopOutlined />,
};

export function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();
    const { settings } = useSettings();
    const { modal, message } = AntdApp.useApp();
    const [sessions, setSessions] = useState<SessionSummary[]>([]);
    const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
    const [loadingSessions, setLoadingSessions] = useState(true);
    const [sessionRailError, setSessionRailError] = useState<string | null>(null);
    const [sessionRailCollapsed, setSessionRailCollapsed] = useResponsiveSessionRail();
    const [renameTarget, setRenameTarget] = useState<SessionSummary | null>(null);
    const [renameDraft, setRenameDraft] = useState("");
    const [sessionActionLoading, setSessionActionLoading] = useState(false);

    if (!user) {
        return null;
    }

    const navigationItems = getNavigationItems(user.role);
    const isAskRoute = location.pathname === "/";
    const routeNeedsSession = location.pathname === "/" || location.pathname === "/carbon-calc" || location.pathname === "/report";
    const focusModeEnabled = isAskRoute && new URLSearchParams(location.search).get("focus") !== "0";
    const hideAskHeader = isAskRoute && focusModeEnabled;
    const mainShellClassName = [
        "app-shell__main-shell",
        isAskRoute ? "app-shell__main-shell--chat-locked" : null,
        routeNeedsSession ? "app-shell__main-shell--workbench" : null,
        sessionRailCollapsed && routeNeedsSession ? "app-shell__main-shell--workbench-collapsed" : null,
    ].filter(Boolean).join(" ");
    const shellClassName = [
        "app-shell",
        focusModeEnabled ? "app-shell--focus" : null,
        isAskRoute ? "app-shell--chat-locked" : null,
        routeNeedsSession ? "app-shell--workbench" : null,
        sessionRailCollapsed && routeNeedsSession ? "app-shell--workbench-collapsed" : null,
    ].filter(Boolean).join(" ");
    const contentClassName = [
        "app-shell__content",
        focusModeEnabled ? "app-shell__content--focus" : null,
        isAskRoute ? "app-shell__content--chat-locked" : null,
        hideAskHeader ? "app-shell__content--headerless" : null,
        routeNeedsSession ? "app-shell__content--workbench" : null,
        sessionRailCollapsed && routeNeedsSession ? "app-shell__content--workbench-collapsed" : null,
    ].filter(Boolean).join(" ");

    useEffect(() => {
        void bootstrapSessionRail(routeNeedsSession);
    }, [routeNeedsSession]);

    useEffect(() => {
        if (!routeNeedsSession || !settings || typeof window === "undefined") {
            return;
        }
        if (window.innerWidth <= 1200) {
            setSessionRailCollapsed(true);
            return;
        }
        setSessionRailCollapsed(settings.appearance.sidebar_default === "collapsed");
    }, [routeNeedsSession, settings?.appearance.sidebar_default, setSessionRailCollapsed]);

    async function bootstrapSessionRail(shouldCreateSession: boolean) {
        setLoadingSessions(true);
        try {
            let sessionList = await listSessions();
            if (!sessionList.length && shouldCreateSession) {
                const created = await createSession();
                sessionList = [created];
            }
            setSessionRailError(null);
            setSessions(sessionList);
            setActiveSessionId((current) => {
                if (!sessionList.length) {
                    return null;
                }
                if (current && sessionList.some((item) => item.session_id === current)) {
                    return current;
                }
                return sessionList[0].session_id;
            });
        } catch {
            setSessionRailError("当前无法读取对话列表。");
            setSessions([]);
            setActiveSessionId(null);
        } finally {
            setLoadingSessions(false);
        }
    }

    async function refreshSessions(preferredSessionId?: string | null) {
        try {
            let sessionList = await listSessions();
            if (!sessionList.length && routeNeedsSession) {
                const created = await createSession();
                sessionList = [created];
            }
            setSessionRailError(null);
            setSessions(sessionList);
            setActiveSessionId((current) => {
                if (!sessionList.length) {
                    return null;
                }
                const targetId = preferredSessionId ?? current;
                if (targetId && sessionList.some((item) => item.session_id === targetId)) {
                    return targetId;
                }
                return sessionList[0].session_id;
            });
            return sessionList;
        } catch {
            setSessionRailError("当前无法读取对话列表。");
            setSessions([]);
            setActiveSessionId(null);
            return [];
        }
    }

    async function handleCreateSession() {
        try {
            const created = await createSession();
            await refreshSessions(created.session_id);
        } catch {
            setSessionRailError("当前无法创建新对话。");
        }
    }

    function handleSelectSession(sessionId: string) {
        setActiveSessionId(sessionId);
        if (typeof window !== "undefined" && window.innerWidth <= 1200) {
            setSessionRailCollapsed(true);
        }
    }

    function handleToggleSessionRail() {
        setSessionRailCollapsed((current) => !current);
    }

    function handleRequestRenameSession(session: SessionSummary) {
        setRenameTarget(session);
        setRenameDraft(session.title);
    }

    async function handleConfirmRenameSession() {
        if (!renameTarget) {
            return;
        }
        const nextTitle = renameDraft.trim();
        if (!nextTitle) {
            setSessionRailError("会话标题不能为空。");
            return;
        }
        setSessionActionLoading(true);
        try {
            const updated = await updateSession(renameTarget.session_id, { title: nextTitle });
            setRenameTarget(null);
            setRenameDraft("");
            await refreshSessions(updated.session_id);
        } catch {
            setSessionRailError("当前无法重命名会话。");
        } finally {
            setSessionActionLoading(false);
        }
    }

    async function handleTogglePinSession(session: SessionSummary) {
        try {
            const updated = await updateSession(session.session_id, { is_pinned: !session.is_pinned });
            await refreshSessions(updated.session_id);
        } catch {
            setSessionRailError("当前无法更新会话置顶状态。");
        }
    }

    function handleDeleteSession(session: SessionSummary) {
        modal.confirm({
            title: "删除这个会话？",
            content: `“${session.title}” 删除后不可恢复。`,
            okText: "删除",
            okButtonProps: { danger: true },
            cancelText: "取消",
            async onOk() {
                try {
                    await deleteSession(session.session_id);
                    const remaining = await refreshSessions(
                        activeSessionId === session.session_id ? null : activeSessionId,
                    );
                    if (!remaining.length) {
                        message.info("当前没有会话，已准备创建新对话。");
                    }
                } catch {
                    setSessionRailError("当前无法删除会话。");
                    throw new Error("delete session failed");
                }
            },
        });
    }

    const outletContext: WorkbenchShellContextValue = {
        sessions,
        activeSessionId,
        loadingSessions,
        sessionRailCollapsed,
        createSession: handleCreateSession,
        refreshSessions,
        selectSession: handleSelectSession,
        toggleSessionRail: handleToggleSessionRail,
    };

    async function handleLogout() {
        await logout();
        navigate("/login", { replace: true });
    }

    const siderUserMenu = (
        <div className="app-shell__focus-user-menu">
            <Space align="start" size={12}>
                <Avatar size={44}>{user.username.slice(0, 1).toUpperCase()}</Avatar>
                <div className="app-shell__focus-user-copy">
                    <Typography.Text strong>{user.username}</Typography.Text>
                    <Tag color={user.role === "admin" ? "purple" : "blue"}>
                        {user.role === "admin" ? "管理员模式" : "个人空间"}
                    </Tag>
                </div>
            </Space>
            <Space direction="vertical" size={8} style={{ width: "100%" }}>
                <Button block icon={<SettingOutlined />} onClick={() => navigate("/settings")}>
                    通用设置
                </Button>
                {user.role === "admin" ? (
                    <Button block icon={<DesktopOutlined />} onClick={() => navigate(ADMIN_NAV_ITEM.path)}>
                        管理后台
                    </Button>
                ) : null}
                <Button block icon={<LogoutOutlined />} onClick={() => void handleLogout()}>
                    退出登录
                </Button>
            </Space>
        </div>
    );

    return (
        <Layout className={shellClassName}>
            <Sider
                breakpoint="lg"
                collapsedWidth={72}
                collapsed={sessionRailCollapsed}
                width={304}
                className={focusModeEnabled ? "app-shell__sider app-shell__sider--focus" : "app-shell__sider"}
            >
                <div className={sessionRailCollapsed ? "app-shell__brand app-shell__brand--compact" : "app-shell__brand"}>
                    {sessionRailCollapsed ? (
                        <>
                            <Typography.Title level={5}>CR</Typography.Title>
                            <Typography.Text type="secondary">对话</Typography.Text>
                        </>
                    ) : (
                        <Typography.Title level={4}>CarbonRag</Typography.Title>
                    )}
                </div>
                <div className="app-shell__sider-nav">
                    <Menu
                        mode="inline"
                        selectedKeys={[location.pathname]}
                        items={navigationItems.map((item) => ({
                            key: item.path,
                            icon: iconMap[item.path as keyof typeof iconMap],
                            label: item.label,
                        }))}
                        onClick={({ key }) => navigate(key)}
                    />
                </div>
                <div className="app-shell__session-region">
                    <SessionRail
                        sessions={sessions}
                        activeSessionId={activeSessionId}
                        collapsed={sessionRailCollapsed}
                        loading={loadingSessions}
                        emptyText={sessionRailError ?? "当前还没有对话。"}
                        onCreateSession={() => void handleCreateSession()}
                        onSelectSession={handleSelectSession}
                        onToggleCollapsed={handleToggleSessionRail}
                        onRenameSession={handleRequestRenameSession}
                        onTogglePinSession={(session) => void handleTogglePinSession(session)}
                        onDeleteSession={handleDeleteSession}
                    />
                </div>
                <div className="app-shell__sider-footer">
                    <Popover trigger="click" placement="rightBottom" content={siderUserMenu}>
                        <Button
                            className={sessionRailCollapsed
                                ? "app-shell__focus-user-trigger"
                                : "app-shell__focus-user-trigger app-shell__focus-user-trigger--expanded"}
                            aria-label="打开当前用户菜单"
                        >
                            <span className="app-shell__focus-user-inline">
                                <Avatar size={34}>{user.username.slice(0, 1).toUpperCase()}</Avatar>
                                {!sessionRailCollapsed ? (
                                    <span className="app-shell__focus-user-name">
                                        <Typography.Text strong ellipsis>
                                            {user.username}
                                        </Typography.Text>
                                    </span>
                                ) : null}
                            </span>
                        </Button>
                    </Popover>
                </div>
            </Sider>
            <Layout className={mainShellClassName}>
                {!hideAskHeader ? (
                    <Header className={focusModeEnabled ? "app-shell__header app-shell__header--focus" : "app-shell__header"}>
                        <div className={focusModeEnabled ? "app-shell__header-bar app-shell__header-bar--focus" : "app-shell__header-bar"}>
                            <div className={focusModeEnabled ? "app-shell__header-copy app-shell__header-copy--focus" : "app-shell__header-copy"}>
                                {focusModeEnabled ? (
                                    <>
                                        <Typography.Text strong>专注对话</Typography.Text>
                                        <Typography.Text type="secondary">
                                            对话优先，依据与系统状态按需展开。
                                        </Typography.Text>
                                    </>
                                ) : (
                                    <>
                                        <Typography.Title level={3}>CarbonRag 工作台</Typography.Title>
                                        <Typography.Paragraph>
                                            当前账号下的问答、知识、核算与报告工作区。
                                        </Typography.Paragraph>
                                    </>
                                )}
                            </div>
                        </div>
                    </Header>
                ) : null}
                <Content className={contentClassName}>
                    <Outlet context={outletContext} />
                </Content>
            </Layout>
            <Modal
                title="重命名会话"
                open={Boolean(renameTarget)}
                okText="保存"
                cancelText="取消"
                confirmLoading={sessionActionLoading}
                onOk={() => void handleConfirmRenameSession()}
                onCancel={() => {
                    if (!sessionActionLoading) {
                        setRenameTarget(null);
                        setRenameDraft("");
                    }
                }}
            >
                <Input
                    value={renameDraft}
                    maxLength={48}
                    autoFocus
                    placeholder="输入新的会话标题"
                    onChange={(event) => setRenameDraft(event.target.value)}
                    onPressEnter={() => void handleConfirmRenameSession()}
                />
            </Modal>
        </Layout>
    );
}
