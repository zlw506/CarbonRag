import { Alert, Card, Descriptions, Skeleton, Tag, Typography } from "antd";
import { useSystemInfo } from "../hooks/useSystemInfo";

export function SystemInfoPanel() {
    const { info, health, loading, error } = useSystemInfo();

    if (loading) {
        return (
            <Card title="系统连通状态">
                <Skeleton active paragraph={{ rows: 4 }} />
            </Card>
        );
    }

    if (error || !info || !health) {
        return (
            <Alert
                type="warning"
                showIcon
                message="后端暂不可达"
                description="前端稳定壳已就绪，但当前未能读取最小系统信息。请先启动 backend 服务。"
            />
        );
    }

    return (
        <Card title="系统连通状态">
            <Descriptions column={1} size="small">
                <Descriptions.Item label="健康检查">
                    <Tag color={health.status === "ok" ? "green" : "default"}>{health.status}</Tag>
                </Descriptions.Item>
                <Descriptions.Item label="应用名称">{info.app_name}</Descriptions.Item>
                <Descriptions.Item label="版本">{info.version}</Descriptions.Item>
                <Descriptions.Item label="环境">{info.env}</Descriptions.Item>
                <Descriptions.Item label="API 前缀">{info.api_prefix}</Descriptions.Item>
                <Descriptions.Item label="Provider 模式">{info.model_provider_mode}</Descriptions.Item>
                <Descriptions.Item label="时间戳">
                    <Typography.Text code>{info.timestamp}</Typography.Text>
                </Descriptions.Item>
            </Descriptions>
        </Card>
    );
}
