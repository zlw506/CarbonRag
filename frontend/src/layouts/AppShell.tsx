import {
    DesktopOutlined,
    ExperimentOutlined,
    FolderOpenOutlined,
    FileTextOutlined,
    LogoutOutlined,
    SearchOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Layout, Menu, Popover, Space, Tag, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import env from "../app/env";
import { ADMIN_NAV_ITEM, getNavigationItems } from "../constants/navigation";

const { Header, Content, Sider } = Layout;

const iconMap = {
    "/": <SearchOutlined />,
    "/my-knowledge": <FolderOpenOutlined />,
    "/carbon-calc": <ExperimentOutlined />,
    "/report": <FileTextOutlined />,
    "/admin": <DesktopOutlined />,
};

export function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();
    const { user, logout } = useAuth();

    if (!user) {
        return null;
    }

    const navigationItems = getNavigationItems(user.role);
    const isAskRoute = location.pathname === "/";
    const focusModeEnabled = isAskRoute && new URLSearchParams(location.search).get("focus") !== "0";
    const hideAskHeader = isAskRoute && focusModeEnabled;
    const shellClassName = [
        "app-shell",
        focusModeEnabled ? "app-shell--focus" : null,
        isAskRoute ? "app-shell--chat-locked" : null,
    ].filter(Boolean).join(" ");
    const contentClassName = [
        "app-shell__content",
        focusModeEnabled ? "app-shell__content--focus" : null,
        isAskRoute ? "app-shell__content--chat-locked" : null,
        hideAskHeader ? "app-shell__content--headerless" : null,
    ].filter(Boolean).join(" ");
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
                collapsedWidth={focusModeEnabled ? 72 : 0}
                collapsed={focusModeEnabled}
                width={228}
                className={focusModeEnabled ? "app-shell__sider app-shell__sider--focus" : "app-shell__sider"}
            >
                <div className={focusModeEnabled ? "app-shell__brand app-shell__brand--compact" : "app-shell__brand"}>
                    {focusModeEnabled ? (
                        <>
                            <Typography.Title level={5}>CR</Typography.Title>
                            <Typography.Text type="secondary">对话</Typography.Text>
                        </>
                    ) : (
                        <>
                            <Typography.Title level={4}>{env.appTitle}</Typography.Title>
                            <Typography.Paragraph>
                                面向双碳问答、知识检索、核算和报告的工作台。
                            </Typography.Paragraph>
                        </>
                    )}
                </div>
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
                <div className="app-shell__sider-footer">
                    <Popover trigger="click" placement="rightBottom" content={siderUserMenu}>
                        <Button
                            shape="circle"
                            className="app-shell__focus-user-trigger"
                            aria-label="打开当前用户菜单"
                        >
                            <Avatar size={34}>{user.username.slice(0, 1).toUpperCase()}</Avatar>
                        </Button>
                    </Popover>
                </div>
            </Sider>
            <Layout className={isAskRoute ? "app-shell__main-shell app-shell__main-shell--chat-locked" : "app-shell__main-shell"}>
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
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}
