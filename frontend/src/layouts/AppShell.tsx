import { DesktopOutlined, ExperimentOutlined, FileTextOutlined, SearchOutlined } from "@ant-design/icons";
import { Layout, Menu, Typography } from "antd";
import { Outlet, useLocation, useNavigate } from "react-router-dom";
import env from "../app/env";
import { navigationItems } from "../constants/navigation";

const { Header, Content, Sider } = Layout;

const iconMap = {
    "/": <SearchOutlined />,
    "/carbon-calc": <ExperimentOutlined />,
    "/report": <FileTextOutlined />,
    "/admin": <DesktopOutlined />
};

export function AppShell() {
    const location = useLocation();
    const navigate = useNavigate();

    return (
        <Layout className="app-shell">
            <Sider breakpoint="lg" collapsedWidth="0" width={248} className="app-shell__sider">
                <div className="app-shell__brand">
                    <Typography.Title level={4}>{env.appTitle}</Typography.Title>
                    <Typography.Paragraph>
                        v0.1.6 public-policy 首个受控检索接入轮，当前问答已展示公共政策依据。
                    </Typography.Paragraph>
                </div>
                <Menu
                    mode="inline"
                    selectedKeys={[location.pathname]}
                    items={navigationItems.map((item) => ({
                        key: item.path,
                        icon: iconMap[item.path as keyof typeof iconMap],
                        label: item.label
                    }))}
                    onClick={({ key }) => navigate(key)}
                />
            </Sider>
            <Layout>
                <Header className="app-shell__header">
                    <Typography.Title level={3}>CarbonRag Public Policy Grounded Ask</Typography.Title>
                </Header>
                <Content className="app-shell__content">
                    <Outlet />
                </Content>
            </Layout>
        </Layout>
    );
}
