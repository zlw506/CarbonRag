import { Card, Space, Typography } from "antd";

export function AdminPlaceholderPage() {
    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Card>
                <Typography.Title level={2}>管理页占位</Typography.Title>
                <Typography.Paragraph>
                    本页只用于冻结未来后台管理入口的位置，不代表权限系统、租户系统或后台配置能力已实现。
                </Typography.Paragraph>
            </Card>
            <Card title="当前边界">
                <Typography.Paragraph>
                    v0.0.2 仅建立稳定工程壳，当前不进入权限中心、系统配置中心或数据治理后台的业务实现。
                </Typography.Paragraph>
            </Card>
        </Space>
    );
}
