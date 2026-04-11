import {
    DesktopOutlined,
    ExperimentOutlined,
    FolderOpenOutlined,
    FileTextOutlined,
    LogoutOutlined,
    SearchOutlined,
} from "@ant-design/icons";
import { Avatar, Button, Layout, Menu, Space, Tag, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import env from "../app/env";
import { getNavigationItems } from "../constants/navigation";

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

    async function handleLogout() {
        await logout();
        navigate("/login", { replace: true });
    }

    return (
        <Layout className={focusModeEnabled ? "app-shell app-shell--focus" : "app-shell"}>
            <Sider
                breakpoint="lg"
                collapsedWidth={focusModeEnabled ? 88 : 0}
                collapsed={focusModeEnabled}
                width={248}
                className={focusModeEnabled ? "app-shell__sider app-shell__sider--focus" : "app-shell__sider"}
            >
                <div className={focusModeEnabled ? "app-shell__brand app-shell__brand--compact" : "app-shell__brand"}>
                    {focusModeEnabled ? (
                        <>
                            <Typography.Title level={5}>CR</Typography.Title>
                            <Typography.Text type="secondary">专注对话</Typography.Text>
                        </>
                    ) : (
                        <>
                            <Typography.Title level={4}>{env.appTitle}</Typography.Title>
                            <Typography.Paragraph>
                                企业试用基线，具备用户隔离、受保护工作台和首版管理员入口。
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
            </Sider>
            <Layout>
                <Header className={focusModeEnabled ? "app-shell__header app-shell__header--focus" : "app-shell__header"}>
                    <div className={focusModeEnabled ? "app-shell__header-bar app-shell__header-bar--focus" : "app-shell__header-bar"}>
                        <div className={focusModeEnabled ? "app-shell__header-copy app-shell__header-copy--focus" : "app-shell__header-copy"}>
                            {focusModeEnabled ? (
                                <>
                                    <Typography.Text strong>专注对话模式</Typography.Text>
                                    <Typography.Text type="secondary">
                                        聊天优先显示，依据、状态和工程细节按需展开。
                                    </Typography.Text>
                                </>
                            ) : (
                                <>
                                    <Typography.Title level={3}>CarbonRag 工作台</Typography.Title>
                                    <Typography.Paragraph>
                                        本地账号体系、角色感知访问，以及按登录用户隔离的数据空间。
                                    </Typography.Paragraph>
                                </>
                            )}
                        </div>
                        <Space size={12} wrap>
                            <Avatar>{user.username.slice(0, 1).toUpperCase()}</Avatar>
                            <Typography.Text strong>{user.username}</Typography.Text>
                            <Tag color={user.role === "admin" ? "purple" : "blue"}>
                                {user.role === "admin" ? "管理员" : "普通用户"}
                            </Tag>
                            <Button icon={<LogoutOutlined />} onClick={() => void handleLogout()}>
                                退出登录
                            </Button>
                        </Space>
                    </div>
                </Header>
                <Content className={focusModeEnabled ? "app-shell__content app-shell__content--focus" : "app-shell__content"}>
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}
