import { MenuFoldOutlined, MenuUnfoldOutlined, PlusOutlined } from "@ant-design/icons";
import { Button, Empty, List, Spin, Tooltip, Typography } from "antd";
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
}: SessionRailProps) {
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
                <Tooltip title="新建对话">
                    <Button
                        type="primary"
                        className="chat-session-rail__icon-button"
                        icon={<PlusOutlined />}
                        onClick={onCreateSession}
                        aria-label="新建会话"
                    />
                </Tooltip>
            </div>

            <div className="chat-session-rail__body">
                {loading ? (
                    <div className="chat-workbench__loading"><Spin /></div>
                ) : sessions.length ? (
                    <List
                        className={collapsed ? "chat-session-list chat-session-list--collapsed" : "chat-session-list"}
                        dataSource={sessions}
                        locale={{ emptyText }}
                        renderItem={(session) => (
                            <List.Item
                                className={activeSessionId === session.session_id
                                    ? "chat-session-list__item chat-session-list__item--active"
                                    : "chat-session-list__item"}
                                onClick={() => onSelectSession(session.session_id)}
                            >
                                {collapsed ? (
                                    <Tooltip title={session.title}>
                                        <div className="chat-session-list__mini">
                                            <Typography.Text strong>{buildSessionMiniTitle(session.title)}</Typography.Text>
                                        </div>
                                    </Tooltip>
                                ) : (
                                    <div className="chat-session-list__content">
                                        <Typography.Text strong>{session.title}</Typography.Text>
                                    </div>
                                )}
                            </List.Item>
                        )}
                    />
                ) : (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={emptyText} />
                )}
            </div>
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

function buildSessionMiniTitle(title: string) {
    const normalized = title.replace(/\s+/g, "").trim();
    return (normalized || "会话").slice(0, 2);
}
