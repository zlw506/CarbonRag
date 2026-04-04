import { Card, Col, Row, Space, Typography } from "antd";
import { SystemInfoPanel } from "./SystemInfoPanel";

interface PageScaffoldProps {
    title: string;
    description: string;
    formTitle: string;
    resultTitle: string;
}

export function PageScaffold({ title, description, formTitle, resultTitle }: PageScaffoldProps) {
    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Card>
                <Typography.Title level={2}>{title}</Typography.Title>
                <Typography.Paragraph>{description}</Typography.Paragraph>
            </Card>
            <SystemInfoPanel />
            <Row gutter={[16, 16]}>
                <Col xs={24} xl={12}>
                    <Card title={formTitle}>
                        <Typography.Paragraph>
                            本区域仍处于占位状态，本轮不实现真实业务字段与提交逻辑。
                        </Typography.Paragraph>
                    </Card>
                </Col>
                <Col xs={24} xl={12}>
                    <Card title={resultTitle}>
                        <Typography.Paragraph>
                            本区域仍处于占位状态，本轮不展示真实核算或报告内容。
                        </Typography.Paragraph>
                    </Card>
                </Col>
            </Row>
        </Space>
    );
}
