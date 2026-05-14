import { CopyOutlined, DownloadOutlined, FileTextOutlined, LinkOutlined } from "@ant-design/icons";
import { Alert, Button, Descriptions, Drawer, Empty, List, Space, Spin, Tabs, Tag, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { buildFilePreviewRawUrl, getFilePreview } from "../services/filePreview";
import type { FilePreviewResponse, FilePreviewTarget } from "../types/filePreview";

interface FilePreviewDrawerProps {
    open: boolean;
    target: FilePreviewTarget | null;
    onClose: () => void;
}

const sourceTypeLabels: Record<string, string> = {
    session_file: "聊天附件",
    rag_document: "知识库文档",
    crawler_candidate: "爬虫候选文件",
    knowledge_item: "知识条目",
};

function formatSize(size?: number | null) {
    if (!size) {
        return "-";
    }
    if (size < 1024) {
        return `${size} B`;
    }
    if (size < 1024 * 1024) {
        return `${(size / 1024).toFixed(1)} KiB`;
    }
    return `${(size / 1024 / 1024).toFixed(1)} MiB`;
}

function renderRawPreview(preview: FilePreviewResponse, target: FilePreviewTarget) {
    if (!preview.raw_available || !preview.raw_preview_url) {
        return <Empty description="没有可预览的原始文件" />;
    }
    const rawUrl = buildFilePreviewRawUrl(target);
    const mime = preview.mime_type ?? "";
    if (mime.startsWith("image/")) {
        return <img src={rawUrl} alt={preview.title} style={{ maxWidth: "100%", borderRadius: 12 }} />;
    }
    if (mime === "application/pdf" || mime.startsWith("text/")) {
        return <iframe title={preview.title} src={rawUrl} style={{ width: "100%", height: "68vh", border: "1px solid #edf0f2", borderRadius: 12 }} />;
    }
    return (
        <Alert
            type="info"
            showIcon
            message="该格式暂不做原版在线渲染"
            description="DOCX / XLSX / PPTX 先展示解析预览、纯文本和检索片段；需要原文件时可下载查看。"
        />
    );
}

export function FilePreviewDrawer({ open, target, onClose }: FilePreviewDrawerProps) {
    const [preview, setPreview] = useState<FilePreviewResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!open || !target) {
            return;
        }
        let cancelled = false;
        setLoading(true);
        setError(null);
        getFilePreview(target)
            .then((result) => {
                if (!cancelled) {
                    setPreview(result);
                }
            })
            .catch((err) => {
                if (!cancelled) {
                    setPreview(null);
                    setError(err?.response?.data?.detail ?? err?.message ?? "文件预览加载失败");
                }
            })
            .finally(() => {
                if (!cancelled) {
                    setLoading(false);
                }
            });
        return () => {
            cancelled = true;
        };
    }, [open, target?.sourceType, target?.sourceId, target?.kbId]);

    const rawUrl = useMemo(() => (target && preview?.raw_available ? buildFilePreviewRawUrl(target) : null), [preview?.raw_available, target]);

    async function copyText(text?: string | null) {
        if (!text) {
            return;
        }
        await navigator.clipboard.writeText(text);
        message.success("已复制");
    }

    const title = preview?.title ?? "文件预览";

    return (
        <Drawer
            open={open}
            width={900}
            title={
                <Space direction="vertical" size={2}>
                    <Space wrap>
                        <FileTextOutlined />
                        <Typography.Text strong>{title}</Typography.Text>
                        {preview ? <Tag>{sourceTypeLabels[preview.source_type] ?? preview.source_type}</Tag> : null}
                    </Space>
                    {preview?.filename ? <Typography.Text type="secondary">{preview.filename}</Typography.Text> : null}
                </Space>
            }
            onClose={onClose}
            extra={
                <Space>
                    {preview?.source_url ? (
                        <Button icon={<LinkOutlined />} href={preview.source_url} target="_blank" rel="noreferrer">
                            打开原网页
                        </Button>
                    ) : null}
                    {rawUrl ? (
                        <Button icon={<DownloadOutlined />} href={rawUrl} target="_blank" rel="noreferrer">
                            原文件
                        </Button>
                    ) : null}
                </Space>
            }
        >
            {loading ? <Spin /> : null}
            {error ? <Alert type="error" showIcon message={error} /> : null}
            {!loading && !error && preview ? (
                <Space direction="vertical" size="large" style={{ width: "100%" }}>
                    {preview.truncated ? <Alert type="warning" showIcon message="预览内容较长，当前只展示前 250000 字符。" /> : null}
                    <Descriptions size="small" column={2} bordered>
                        <Descriptions.Item label="状态">{preview.status}</Descriptions.Item>
                        <Descriptions.Item label="MIME">{preview.mime_type ?? "-"}</Descriptions.Item>
                        <Descriptions.Item label="大小">{formatSize(preview.size)}</Descriptions.Item>
                        <Descriptions.Item label="片段数">{preview.chunks.length}</Descriptions.Item>
                    </Descriptions>
                    <Tabs
                        items={[
                            {
                                key: "markdown",
                                label: "解析预览",
                                children: preview.markdown ? (
                                    <div className="markdown-body">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{preview.markdown}</ReactMarkdown>
                                    </div>
                                ) : (
                                    <Empty description="暂无 Markdown 解析结果" />
                                ),
                            },
                            {
                                key: "text",
                                label: "纯文本",
                                children: preview.text ? (
                                    <Space direction="vertical" style={{ width: "100%" }}>
                                        <Button icon={<CopyOutlined />} onClick={() => void copyText(preview.text)}>
                                            复制全文
                                        </Button>
                                        <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>{preview.text}</Typography.Paragraph>
                                    </Space>
                                ) : (
                                    <Empty description="暂无纯文本" />
                                ),
                            },
                            {
                                key: "chunks",
                                label: `检索片段 ${preview.chunks.length}`,
                                children: preview.chunks.length ? (
                                    <List
                                        dataSource={preview.chunks}
                                        renderItem={(chunk) => (
                                            <List.Item>
                                                <Space direction="vertical" style={{ width: "100%" }}>
                                                    <Space wrap>
                                                        <Tag>#{chunk.order_index + 1}</Tag>
                                                        {chunk.vector_status ? <Tag color={chunk.vector_status === "indexed" ? "green" : "default"}>{chunk.vector_status}</Tag> : null}
                                                        {chunk.page_number ? <Tag>p.{chunk.page_number}</Tag> : null}
                                                        {chunk.sheet_name ? <Tag>{chunk.sheet_name}</Tag> : null}
                                                        {chunk.section_title ? <Tag>{chunk.section_title}</Tag> : null}
                                                    </Space>
                                                    <Typography.Paragraph style={{ whiteSpace: "pre-wrap", marginBottom: 0 }}>{chunk.text}</Typography.Paragraph>
                                                </Space>
                                            </List.Item>
                                        )}
                                    />
                                ) : (
                                    <Empty description="暂无检索片段" />
                                ),
                            },
                            {
                                key: "raw",
                                label: "原始文件",
                                children: target ? renderRawPreview(preview, target) : null,
                            },
                            {
                                key: "metadata",
                                label: "元数据",
                                children: (
                                    <Typography.Paragraph style={{ whiteSpace: "pre-wrap" }}>
                                        {JSON.stringify(preview.metadata, null, 2)}
                                    </Typography.Paragraph>
                                ),
                            },
                        ]}
                    />
                </Space>
            ) : null}
        </Drawer>
    );
}
