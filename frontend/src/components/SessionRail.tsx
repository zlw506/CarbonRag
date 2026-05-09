import {
    DeleteOutlined,
    DownOutlined,
    EditOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    MoreOutlined,
    PlusOutlined,
    PushpinOutlined,
    UpOutlined,
} from "@ant-design/icons";
import { Button, Dropdown, Empty, List, Spin, Tooltip, Typography } from "antd";
import { useEffect, useState } from "react";
import type { SessionSummary } from "../types/session";

interface SessionRailProps {
    sessions: SessionSummary[];
    activeSessionId: string | null;
    collapsed: boolean;
    loading: boolean;
    emptyText?: string;
    onCreateSession: () => void;
    onSelectSession: (sessionId: string) => void;
    onToggleCollapsed: () => void;
    onRenameSession: (session: SessionSummary) => void;
    onTogglePinSession: (session: SessionSummary) => void;
    onDeleteSession: (session: SessionSummary) => void;
}

export function SessionRail({
    sessions,
    activeSessionId,
    collapsed,
    loading,
    emptyText = "当前还没有会话。",
    onCreateSession,
    onSelectSession,
    onToggleCollapsed,
    onRenameSession,
    onTogglePinSession,
    onDeleteSession,
}: SessionRailProps) {
    const [recentCollapsed, setRecentCollapsed] = useState(false);

    return (
        <div className={collapsed ? "chat-session-rail chat-session-rail--collapsed" : "chat-session-rail"}>
            <div className="chat-session-rail__header">
                <Tooltip title={collapsed ? "展开会话栏" : "收起会话栏"}>
                    <Button
                        className="chat-session-rail__icon-button"
                        icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
                        onClick={onToggleCollapsed}
                        aria-label={collapsed ? "展开会话栏" : "收起会话栏"}
                    />
                </Tooltip>
                {collapsed ? (
                    <Tooltip title="新建对话">
                        <Button
                            type="primary"
                            className="chat-session-rail__icon-button"
                            icon={<PlusOutlined />}
                            onClick={onCreateSession}
                            aria-label="新建会话"
                        />
                    </Tooltip>
                ) : (
                    <Button
                        type="primary"
                        className="chat-session-rail__create-button"
                        icon={<PlusOutlined />}
                        onClick={onCreateSession}
                    >
                        新建对话
                    </Button>
                )}
            </div>

            {!collapsed ? (
                <div className="chat-session-rail__body">
                    {loading ? (
                        <div className="chat-workbench__loading"><Spin /></div>
                    ) : sessions.length ? (
                        <div className="chat-session-rail__scroll">
                            <button
                                type="button"
                                className="chat-session-rail__section-title"
                                aria-expanded={!recentCollapsed}
                                aria-label={recentCollapsed ? "展开最近会话" : "收起最近会话"}
                                onClick={() => setRecentCollapsed((current) => !current)}
                            >
                                <span>最近</span>
                                {recentCollapsed ? <UpOutlined /> : <DownOutlined />}
                            </button>
                            {!recentCollapsed ? (
                                <List
                                    className="chat-session-list"
                                    dataSource={sessions}
                                    locale={{ emptyText }}
                                    renderItem={(session) => (
                                        <List.Item
                                            className={activeSessionId === session.session_id
                                                ? "chat-session-list__item chat-session-list__item--active"
                                                : "chat-session-list__item"}
                                            onClick={() => onSelectSession(session.session_id)}
                                        >
                                            <div className="chat-session-list__row">
                                                <div className="chat-session-list__content">
                                                    <Typography.Text
                                                        className="chat-session-list__title"
                                                        ellipsis={{ tooltip: session.title }}
                                                    >
                                                        {session.title}
                                                    </Typography.Text>
                                                </div>
                                                <div className="chat-session-list__actions" onClick={(event) => event.stopPropagation()}>
                                                    {session.is_pinned ? (
                                                        <Tooltip title="已置顶">
                                                            <PushpinOutlined className="chat-session-list__pin-icon" />
                                                        </Tooltip>
                                                    ) : null}
                                                    <Dropdown
                                                        trigger={["click"]}
                                                        placement="bottomRight"
                                                        menu={{
                                                            items: [
                                                                {
                                                                    key: "rename",
                                                                    icon: <EditOutlined />,
                                                                    label: "重命名",
                                                                },
                                                                {
                                                                    key: "pin",
                                                                    icon: <PushpinOutlined />,
                                                                    label: session.is_pinned ? "取消置顶" : "置顶",
                                                                },
                                                                {
                                                                    type: "divider",
                                                                },
                                                                {
                                                                    key: "delete",
                                                                    icon: <DeleteOutlined />,
                                                                    label: "删除",
                                                                    danger: true,
                                                                },
                                                            ],
                                                            onClick: ({ key, domEvent }) => {
                                                                domEvent.stopPropagation();
                                                                if (key === "rename") {
                                                                    onRenameSession(session);
                                                                    return;
                                                                }
                                                                if (key === "pin") {
                                                                    onTogglePinSession(session);
                                                                    return;
                                                                }
                                                                if (key === "delete") {
                                                                    onDeleteSession(session);
                                                                }
                                                            },
                                                        }}
                                                    >
                                                        <Button
                                                            type="text"
                                                            size="small"
                                                            className="chat-session-list__more"
                                                            icon={<MoreOutlined />}
                                                            aria-label={`打开 ${session.title} 的会话菜单`}
                                                        />
                                                    </Dropdown>
                                                </div>
                                            </div>
                                        </List.Item>
                                    )}
                                />
                            ) : null}
                        </div>
                    ) : (
                        <div className="chat-session-rail__empty">
                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
                        </div>
                    )}
                </div>
            ) : null}
        </div>
    );
}

export function useResponsiveSessionRail() {
    const [collapsed, setCollapsed] = useState(false);

    useEffect(() => {
        if (typeof window === "undefined") {
            return;
        }

        const syncCollapsedState = () => {
            setCollapsed((current) => {
                if (window.innerWidth <= 1200) {
                    return true;
                }
                if (window.innerWidth >= 1440) {
                    return current;
                }
                return current;
            });
        };

        syncCollapsedState();
        window.addEventListener("resize", syncCollapsedState);
        return () => window.removeEventListener("resize", syncCollapsedState);
    }, []);

    return [collapsed, setCollapsed] as const;
}
