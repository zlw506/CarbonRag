import { useState } from "react";
import { Alert, Button, Card, Descriptions, Input, Space, Tag, Typography } from "antd";
import { SystemInfoPanel } from "../../components/SystemInfoPanel";
import { submitAskRequest } from "../../services/ask";
import type { AskResponse } from "../../types/ask";

export function AskPage() {
    const [question, setQuestion] = useState("");
    const [result, setResult] = useState<AskResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [transportError, setTransportError] = useState<string | null>(null);

    async function handleSubmit() {
        setLoading(true);
        setTransportError(null);

        try {
            const response = await submitAskRequest({
                question,
                knowledge_scope: "public",
                top_k: 5,
            });
            setResult(response);
        } catch (error) {
            if (isAskResponse(error)) {
                setResult(error);
            } else {
                setResult(null);
                setTransportError("后端 ask 服务暂不可达，请确认 backend 已启动且 provider 可用。");
            }
        } finally {
            setLoading(false);
        }
    }

    return (
        <Space direction="vertical" size={16} style={{ width: "100%" }}>
            <Card>
                <Typography.Title level={2}>问答页</Typography.Title>
                <Typography.Paragraph>
                    v0.1.5B 已联通 `POST /api/v1/ask`。当前只支持单轮通用双碳问答，不接 RAG、不接企业私有数据，`citations` 暂为空数组占位。
                </Typography.Paragraph>
            </Card>
            <SystemInfoPanel />
            {transportError ? (
                <Alert
                    type="error"
                    showIcon
                    message="请求失败"
                    description={transportError}
                />
            ) : null}
            <Card title="问题输入区">
                <Space direction="vertical" size={16} style={{ width: "100%" }}>
                    <Typography.Paragraph>
                        当前固定使用 `knowledge_scope=public` 与 `top_k=5`，仅验证首条 ask-mode 真实链路。
                    </Typography.Paragraph>
                    <Input.TextArea
                        value={question}
                        onChange={(event) => setQuestion(event.target.value)}
                        rows={6}
                        maxLength={2000}
                        placeholder="例如：什么是双碳目标？"
                    />
                    <Button type="primary" onClick={handleSubmit} loading={loading}>
                        提交到 /api/v1/ask
                    </Button>
                </Space>
            </Card>
            <Card title="答案与引用区">
                {result ? (
                    <Space direction="vertical" size={16} style={{ width: "100%" }}>
                        <Descriptions column={1} size="small">
                            <Descriptions.Item label="状态">
                                <Tag color={statusColorMap[result.status]}>{result.status}</Tag>
                            </Descriptions.Item>
                            <Descriptions.Item label="模式">{result.mode}</Descriptions.Item>
                            <Descriptions.Item label="Trace ID">
                                <Typography.Text code>{result.trace_id}</Typography.Text>
                            </Descriptions.Item>
                        </Descriptions>
                        <Card size="small" title="答案">
                            <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>
                                {result.answer}
                            </Typography.Paragraph>
                        </Card>
                        <Card size="small" title="Citations">
                            {result.citations.length === 0 ? (
                                <Typography.Paragraph style={{ marginBottom: 0 }}>
                                    当前未接入 RAG 与真实引用生成，`citations` 为空数组占位。
                                </Typography.Paragraph>
                            ) : null}
                        </Card>
                    </Space>
                ) : (
                    <Typography.Paragraph style={{ marginBottom: 0 }}>
                        提交一次问题后，这里会展示后端 ask mode 返回的答案、状态和 trace_id。
                    </Typography.Paragraph>
                )}
            </Card>
        </Space>
    );
}

const statusColorMap = {
    ok: "green",
    provider_error: "red",
    invalid_input: "gold",
} as const;

function isAskResponse(value: unknown): value is AskResponse {
    if (!value || typeof value !== "object") {
        return false;
    }

    const candidate = value as Partial<AskResponse>;
    return (
        candidate.mode === "ask" &&
        typeof candidate.answer === "string" &&
        typeof candidate.trace_id === "string" &&
        Array.isArray(candidate.citations)
    );
}
