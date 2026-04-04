import { useState } from "react";
import { Alert, Button, Card, Descriptions, Input, List, Space, Tag, Typography } from "antd";
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
                    v0.1.6 已把 `POST /api/v1/ask` 升级为带公共政策样本 grounding 的单轮问答链路。当前 citations 来自本地公共政策样本语料，仍未接入企业私有数据与完整知识库。
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
                        当前固定使用 `knowledge_scope=public` 与 `top_k=5`，仅验证公共政策样本检索 grounding 链路。
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
                                    当前公共政策样本中没有检索到足够依据，系统已返回受限回答。本轮 citations 仅来自本地公共政策样本语料，不代表完整知识库覆盖。
                                </Typography.Paragraph>
                            ) : (
                                <List
                                    dataSource={result.citations}
                                    renderItem={(citation) => (
                                        <List.Item key={citation.chunk_id}>
                                            <Space direction="vertical" size={4} style={{ width: "100%" }}>
                                                <Space size={8} wrap>
                                                    <Typography.Text strong>{citation.title}</Typography.Text>
                                                    <Tag>{citation.source}</Tag>
                                                    <Typography.Text type="secondary">
                                                        {citation.chunk_id}
                                                    </Typography.Text>
                                                </Space>
                                                <Typography.Paragraph
                                                    style={{ marginBottom: 0, whiteSpace: "pre-wrap" }}
                                                >
                                                    {citation.snippet}
                                                </Typography.Paragraph>
                                                {citation.source_url ? (
                                                    <Typography.Link href={citation.source_url} target="_blank" rel="noreferrer">
                                                        查看来源
                                                    </Typography.Link>
                                                ) : (
                                                    <Typography.Text type="secondary">
                                                        来源标识：{citation.doc_id}
                                                    </Typography.Text>
                                                )}
                                            </Space>
                                        </List.Item>
                                    )}
                                />
                            )}
                        </Card>
                    </Space>
                ) : (
                    <Typography.Paragraph style={{ marginBottom: 0 }}>
                        提交一次问题后，这里会展示后端 ask mode 返回的答案、状态、trace_id 和公共政策 citations。
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
