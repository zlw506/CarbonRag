import {
    DesktopOutlined,
    ExperimentOutlined,
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

    async function handleLogout() {
        await logout();
        navigate("/login", { replace: true });
    }

    return (
        <Layout className="app-shell">
            <Sider breakpoint="lg" collapsedWidth="0" width={248} className="app-shell__sider">
                <div className="app-shell__brand">
                    <Typography.Title level={4}>{env.appTitle}</Typography.Title>
                    <Typography.Paragraph>
                        Enterprise trial baseline with user isolation, protected workspaces, and an initial admin
                        console.
                    </Typography.Paragraph>
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
                <Header className="app-shell__header">
                    <div className="app-shell__header-bar">
                        <div>
                            <Typography.Title level={3}>CarbonRag Workbench</Typography.Title>
                            <Typography.Paragraph>
                                Local accounts, role-aware access, and isolated data per signed-in user.
                            </Typography.Paragraph>
                        </div>
                        <Space size={12} wrap>
                            <Avatar>{user.username.slice(0, 1).toUpperCase()}</Avatar>
                            <Typography.Text strong>{user.username}</Typography.Text>
                            <Tag color={user.role === "admin" ? "purple" : "blue"}>{user.role}</Tag>
                            <Button icon={<LogoutOutlined />} onClick={() => void handleLogout()}>
                                Logout
                            </Button>
                        </Space>
                    </div>
                </Header>
                <Content className="app-shell__content">
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}
