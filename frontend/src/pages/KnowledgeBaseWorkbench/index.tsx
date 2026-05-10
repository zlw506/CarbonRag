import { ApiOutlined, DatabaseOutlined, FileSearchOutlined, PlayCircleOutlined, PlusOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Empty, Input, List, Select, Space, Spin, Tag, Typography } from "antd";
import { useEffect, useState } from "react";
import {
    chunkKbDocument,
    createKbDocument,
    createKnowledgeBase,
    indexKbDocument,
    listKbDocumentChunks,
    listKbDocuments,
    listKnowledgeBases,
    parseKbDocument,
} from "../../services/kb";
import { listAttachableKnowledgeItems } from "../../services/knowledge";
import { runRagTestQA, searchRagSpine } from "../../services/rag";
import type { KnowledgeItem } from "../../types/knowledge";
import type { KnowledgeBase, RagChunk, RagDocument, RagHit, RagSearchResult, RagTestQAResult } from "../../types/kb";

export function KnowledgeBaseWorkbench() {
    const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
    const [activeKbId, setActiveKbId] = useState<string | undefined>();
    const [documents, setDocuments] = useState<RagDocument[]>([]);
    const [chunks, setChunks] = useState<RagChunk[]>([]);
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
    const [newKbName, setNewKbName] = useState("企业知识库");
    const [selectedKnowledgeItemId, setSelectedKnowledgeItemId] = useState<string | undefined>();
    const [query, setQuery] = useState("双碳目标有哪些关键要求？");
    const [searchResult, setSearchResult] = useState<RagSearchResult | null>(null);
    const [qaResult, setQaResult] = useState<RagTestQAResult | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        void bootstrap();
    }, []);

    useEffect(() => {
        if (activeKbId) {
            void loadDocuments(activeKbId);
        }
    }, [activeKbId]);

    async function bootstrap() {
        setLoading(true);
        setError(null);
        try {
            const [nextKbs, items] = await Promise.all([listKnowledgeBases(), listAttachableKnowledgeItems()]);
            setKbs(nextKbs);
            setActiveKbId(nextKbs[0]?.kb_id);
            setKnowledgeItems(items);
        } catch {
            setError("当前无法加载知识库工作台。");
        } finally {
            setLoading(false);
        }
    }

    async function loadDocuments(kbId: string) {
        setLoading(true);
        setError(null);
        try {
            const docs = await listKbDocuments(kbId);
            setDocuments(docs);
            if (docs[0]) {
                setChunks(await listKbDocumentChunks(kbId, docs[0].doc_id));
            } else {
                setChunks([]);
            }
        } catch {
            setError("当前无法加载知识库文档。");
        } finally {
            setLoading(false);
        }
    }

    async function handleCreateKb() {
        if (!newKbName.trim()) {
            return;
        }
        const kb = await createKnowledgeBase({ name: newKbName.trim() });
        setKbs((current) => [kb, ...current]);
        setActiveKbId(kb.kb_id);
    }

    async function handleImportKnowledgeItem() {
        if (!activeKbId || !selectedKnowledgeItemId) {
            return;
        }
        const doc = await createKbDocument(activeKbId, { knowledge_item_id: selectedKnowledgeItemId });
        setDocuments((current) => [doc, ...current]);
    }

    async function runDocStage(doc: RagDocument, stage: "parse" | "chunk" | "index") {
        if (!activeKbId) {
            return;
        }
        const next =
            stage === "parse"
                ? await parseKbDocument(activeKbId, doc.doc_id)
                : stage === "chunk"
                    ? await chunkKbDocument(activeKbId, doc.doc_id)
                    : await indexKbDocument(activeKbId, doc.doc_id);
        setDocuments((current) => current.map((item) => item.doc_id === next.doc_id ? next : item));
        setChunks(await listKbDocumentChunks(activeKbId, next.doc_id));
    }

    async function handleSearch() {
        if (!query.trim()) {
            return;
        }
        const result = await searchRagSpine({ query, kb_id: activeKbId, mode: "hybrid_rerank" });
        setSearchResult(result);
        setQaResult(null);
    }

    async function handleTestQA() {
        if (!query.trim()) {
            return;
        }
        const result = await runRagTestQA({ query, kb_id: activeKbId, mode: "hybrid_rerank" });
        setQaResult(result);
    }

    return (
        <div className="knowledge-base-workbench">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
                <Card
                    title={<Space><DatabaseOutlined />RAG-Pro 知识库工作台</Space>}
                    extra={<Tag color="green">V1.6.3 spine</Tag>}
                >
                    <Typography.Paragraph type="secondary">
                        这里是新的 RAG 主脊柱入口：知识库、文档状态、chunk 预览、hybrid/RRF、rerank trace 和 test QA。
                    </Typography.Paragraph>
                    {error ? <Alert type="error" showIcon message={error} /> : null}
                    <Space wrap>
                        <Input value={newKbName} onChange={(event) => setNewKbName(event.target.value)} style={{ width: 220 }} />
                        <Button icon={<PlusOutlined />} type="primary" onClick={handleCreateKb}>创建知识库</Button>
                        <Select
                            value={activeKbId}
                            onChange={setActiveKbId}
                            style={{ minWidth: 260 }}
                            options={kbs.map((kb) => ({ value: kb.kb_id, label: `${kb.name}${kb.is_default ? " · 默认" : ""}` }))}
                            placeholder="选择知识库"
                        />
                    </Space>
                </Card>

                <Card title="文档导入与状态机" extra={loading ? <Spin size="small" /> : null}>
                    <Space wrap style={{ marginBottom: 16 }}>
                        <Select
                            showSearch
                            value={selectedKnowledgeItemId}
                            onChange={setSelectedKnowledgeItemId}
                            style={{ minWidth: 360 }}
                            optionFilterProp="label"
                            placeholder="从现有知识条目/上传文件导入"
                            options={knowledgeItems.map((item) => ({ value: item.knowledge_item_id, label: item.title }))}
                        />
                        <Button onClick={handleImportKnowledgeItem} disabled={!activeKbId || !selectedKnowledgeItemId}>导入到知识库</Button>
                    </Space>
                    {documents.length ? (
                        <List
                            dataSource={documents}
                            renderItem={(doc) => (
                                <List.Item
                                    actions={[
                                        <Button size="small" onClick={() => runDocStage(doc, "parse")}>parse</Button>,
                                        <Button size="small" onClick={() => runDocStage(doc, "chunk")}>chunk</Button>,
                                        <Button size="small" type="primary" onClick={() => runDocStage(doc, "index")}>index</Button>,
                                    ]}
                                >
                                    <List.Item.Meta
                                        avatar={<FileSearchOutlined />}
                                        title={<Space>{doc.title}<StatusTag status={doc.status} /></Space>}
                                        description={`parse=${doc.parse_status} · chunk=${doc.chunk_status} · index=${doc.index_status} · chunks=${doc.chunk_count}/${doc.indexed_chunk_count}`}
                                    />
                                </List.Item>
                            )}
                        />
                    ) : <Empty description="暂无文档，先导入一个现有知识条目。" />}
                </Card>

                <Card title="Chunk 预览">
                    {chunks.length ? (
                        <List
                            dataSource={chunks.slice(0, 8)}
                            renderItem={(chunk) => (
                                <List.Item>
                                    <Typography.Paragraph ellipsis={{ rows: 3, expandable: "collapsible", symbol: "展开" }}>
                                        <Typography.Text type="secondary">#{chunk.chunk_index} · {chunk.vector_status}</Typography.Text>
                                        <br />
                                        {chunk.text}
                                    </Typography.Paragraph>
                                </List.Item>
                            )}
                        />
                    ) : <Empty description="选择或 chunk 文档后查看片段。" />}
                </Card>

                <Card title={<Space><ApiOutlined />Test QA 与 Trace</Space>}>
                    <Space.Compact style={{ width: "100%" }}>
                        <Input value={query} onChange={(event) => setQuery(event.target.value)} />
                        <Button icon={<PlayCircleOutlined />} onClick={handleSearch}>检索</Button>
                        <Button type="primary" onClick={handleTestQA}>Test QA</Button>
                    </Space.Compact>
                    {searchResult ? <TracePanel hits={searchResult.hits} trace={searchResult.trace} /> : null}
                    {qaResult ? (
                        <Card size="small" title="回答" style={{ marginTop: 12 }}>
                            <Typography.Paragraph>{qaResult.answer}</Typography.Paragraph>
                            <TracePanel hits={qaResult.hits} trace={qaResult.retrieval_trace} />
                        </Card>
                    ) : null}
                </Card>
            </Space>
        </div>
    );
}

function StatusTag({ status }: { status: string }) {
    const color = status === "indexed" ? "green" : status === "failed" ? "red" : status === "chunked" ? "blue" : "default";
    return <Tag color={color}>{status}</Tag>;
}

function TracePanel({ hits, trace }: { hits: RagHit[]; trace: RagSearchResult["trace"] }) {
    return (
        <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
            <Space wrap>
                <Tag color={trace.degraded ? "orange" : "green"}>backend {trace.vector_backend}</Tag>
                <Tag>dense {trace.dense_count}</Tag>
                <Tag>sparse {trace.sparse_count}</Tag>
                <Tag>rrf {trace.merged_count}</Tag>
                <Tag color={trace.rerank_applied ? "green" : "default"}>rerank {trace.rerank_applied ? "yes" : "no"}</Tag>
            </Space>
            {trace.warnings?.length ? <Alert type="warning" showIcon message={trace.warnings.join("；")} /> : null}
            <List
                size="small"
                dataSource={hits}
                renderItem={(hit) => (
                    <List.Item>
                        <List.Item.Meta
                            title={<Space>{hit.title}<Tag>{hit.source_type}</Tag></Space>}
                            description={
                                <Typography.Paragraph ellipsis={{ rows: 2, expandable: "collapsible", symbol: "展开" }}>
                                    {hit.snippet}
                                </Typography.Paragraph>
                            }
                        />
                        <Typography.Text type="secondary">
                            dense {formatScore(hit.dense_score)} · sparse {formatScore(hit.sparse_score)} · rrf {formatScore(hit.rrf_score)} · rerank {formatScore(hit.rerank_score)}
                        </Typography.Text>
                    </List.Item>
                )}
            />
        </Space>
    );
}

function formatScore(value?: number | null) {
    return typeof value === "number" ? value.toFixed(3) : "-";
}

