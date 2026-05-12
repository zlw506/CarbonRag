import {
    ApiOutlined,
    CloudUploadOutlined,
    DatabaseOutlined,
    FileSearchOutlined,
    PartitionOutlined,
    PlayCircleOutlined,
    PlusOutlined,
    SearchOutlined,
} from "@ant-design/icons";
import { Alert, Button, Card, Empty, Input, List, Progress, Select, Space, Spin, Tag, Typography, Upload } from "antd";
import { useEffect, useMemo, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { useSettings } from "../../app/SettingsContext";
import {
    chunkKbDocument,
    createKbDocument,
    createKnowledgeBase,
    indexKbDocument,
    listKbDocumentChunks,
    listKbDocuments,
    listKnowledgeBases,
    parseKbDocument,
    uploadKbDocument,
} from "../../services/kb";
import { listAttachableKnowledgeItems } from "../../services/knowledge";
import { runRagEval, runRagTestQA, searchRagSpine } from "../../services/rag";
import type { KnowledgeItem } from "../../types/knowledge";
import type { KnowledgeBase, RagChunk, RagDocument, RagEvalRun, RagHit, RagSearchResult, RagTestQAResult } from "../../types/kb";

type StageName = "parse" | "chunk" | "index";

const stageMeta: Record<StageName, { label: string; shortLabel: string; hint: string; icon: ReactNode }> = {
    parse: {
        label: "解析文档",
        shortLabel: "解析",
        hint: "读取原始文件或知识条目的正文，形成可处理文本。",
        icon: <FileSearchOutlined />,
    },
    chunk: {
        label: "生成片段",
        shortLabel: "分块",
        hint: "把长文档切成可检索的小段，并保留页码、表格、章节等定位信息。",
        icon: <PartitionOutlined />,
    },
    index: {
        label: "写入向量库",
        shortLabel: "入库",
        hint: "用 BGE-M3 生成向量并写入 Milvus，之后才能被 RAG 问答命中。",
        icon: <CloudUploadOutlined />,
    },
};

const statusLabelMap: Record<string, string> = {
    uploaded: "已导入，待解析",
    pending: "待处理",
    queued: "排队中",
    running: "处理中",
    parsing: "解析中",
    parsed: "已解析",
    chunked: "已分块",
    indexed: "已入库，可检索",
    failed: "失败",
    parse_failed: "解析失败",
    chunk_failed: "分块失败",
    index_failed: "入库失败",
};

const sourceTypeLabelMap: Record<string, string> = {
    manual: "手动文本",
    private_upload: "个人上传",
    private_sample: "知识条目",
    public_policy: "公共政策",
};

export function KnowledgeBaseWorkbench() {
    const navigate = useNavigate();
    const { getActiveProviderOverride } = useSettings();
    const [kbs, setKbs] = useState<KnowledgeBase[]>([]);
    const [activeKbId, setActiveKbId] = useState<string | undefined>();
    const [activeDocId, setActiveDocId] = useState<string | undefined>();
    const [documents, setDocuments] = useState<RagDocument[]>([]);
    const [chunks, setChunks] = useState<RagChunk[]>([]);
    const [knowledgeItems, setKnowledgeItems] = useState<KnowledgeItem[]>([]);
    const [newKbName, setNewKbName] = useState("企业知识库");
    const [selectedKnowledgeItemId, setSelectedKnowledgeItemId] = useState<string | undefined>();
    const [query, setQuery] = useState("双碳目标有哪些关键要求？");
    const [searchResult, setSearchResult] = useState<RagSearchResult | null>(null);
    const [qaResult, setQaResult] = useState<RagTestQAResult | null>(null);
    const [evalResult, setEvalResult] = useState<RagEvalRun | null>(null);
    const [loading, setLoading] = useState(false);
    const [runningStage, setRunningStage] = useState<string | null>(null);
    const [error, setError] = useState<string | null>(null);

    const activeKb = useMemo(() => kbs.find((item) => item.kb_id === activeKbId), [activeKbId, kbs]);
    const activeDoc = useMemo(() => documents.find((item) => item.doc_id === activeDocId), [activeDocId, documents]);

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
            setError("当前无法加载知识库工作台。请确认后端已启动，并且你已经登录。");
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
            const nextActiveDocId = docs[0]?.doc_id;
            setActiveDocId(nextActiveDocId);
            if (nextActiveDocId) {
                setChunks(await listKbDocumentChunks(kbId, nextActiveDocId));
            } else {
                setChunks([]);
            }
        } catch {
            setError("当前无法加载知识库文档。请确认该知识库仍存在，且你有访问权限。");
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
        setActiveDocId(doc.doc_id);
        setChunks([]);
    }

    async function handleUploadToKb(file: File) {
        if (!activeKbId) {
            setError("请先选择或创建知识库。");
            return false;
        }
        setRunningStage(`upload:${file.name}`);
        setError(null);
        try {
            const doc = await uploadKbDocument(activeKbId, file);
            setDocuments((current) => [doc, ...current]);
            setActiveDocId(doc.doc_id);
            setChunks([]);
        } catch {
            setError("上传到知识库失败。请确认文件格式受支持，且后端文件解析服务正常。");
        } finally {
            setRunningStage(null);
        }
        return false;
    }

    async function handleLoadChunks(doc: RagDocument) {
        if (!activeKbId) {
            return;
        }
        setActiveDocId(doc.doc_id);
        setChunks(await listKbDocumentChunks(activeKbId, doc.doc_id));
    }

    async function runDocStage(doc: RagDocument, stage: StageName) {
        if (!activeKbId) {
            return;
        }
        setRunningStage(`${doc.doc_id}:${stage}`);
        setError(null);
        try {
            const next =
                stage === "parse"
                    ? await parseKbDocument(activeKbId, doc.doc_id)
                    : stage === "chunk"
                        ? await chunkKbDocument(activeKbId, doc.doc_id)
                        : await indexKbDocument(activeKbId, doc.doc_id);
            setDocuments((current) => current.map((item) => item.doc_id === next.doc_id ? next : item));
            setActiveDocId(next.doc_id);
            setChunks(await listKbDocumentChunks(activeKbId, next.doc_id));
        } catch {
            setError(`${stageMeta[stage].label}失败。请检查文档状态、后端日志、Milvus/Docker 是否正常运行。`);
        } finally {
            setRunningStage(null);
        }
    }

    async function handleSearch() {
        if (!query.trim()) {
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const result = await searchRagSpine({ query, kb_id: activeKbId, mode: "hybrid_rerank" });
            setSearchResult(result);
            setQaResult(null);
        } catch {
            setError("检索测试失败。请确认文档已写入向量库，并且 Docker Milvus / BGE 模型可用。");
        } finally {
            setLoading(false);
        }
    }

    async function handleTestQA() {
        if (!query.trim()) {
            return;
        }
        setLoading(true);
        setError(null);
        try {
            const result = await runRagTestQA({
                query,
                kb_id: activeKbId,
                mode: "hybrid_rerank",
                provider_override: getActiveProviderOverride(),
            });
            setQaResult(result);
            setSearchResult(null);
        } catch {
            setError("检索问答测试失败。请先确认检索测试能命中片段。");
        } finally {
            setLoading(false);
        }
    }

    async function handleEval() {
        if (!activeKbId) {
            return;
        }
        setLoading(true);
        setError(null);
        try {
            setEvalResult(await runRagEval({ kb_id: activeKbId, mode: "hybrid_rerank", top_k: 5 }));
        } catch {
            setError("RAG 验收评分失败。请确认青木验收文档已入库并完成向量化。");
        } finally {
            setLoading(false);
        }
    }

    function openAskPageWithCurrentKb() {
        const params = new URLSearchParams();
        if (activeKbId) {
            params.set("kb_id", activeKbId);
        }
        params.set("rag_mode", "hybrid_rerank");
        if (query.trim()) {
            params.set("question", query.trim());
        }
        navigate(`/?${params.toString()}`);
    }

    return (
        <div className="knowledge-base-workbench">
            <Space direction="vertical" size={16} style={{ width: "100%" }}>
                <Card
                    title={<Space><DatabaseOutlined />RAG-Pro 知识库工作台</Space>}
                    extra={<Tag color="green">V1.6.10 Test QA 加固</Tag>}
                >
                    <Typography.Paragraph type="secondary">
                        这里不是普通聊天页，而是 RAG 验收台：先把资料导入知识库，再按“解析文档 → 生成片段 → 写入向量库”处理，最后用检索测试和检索问答确认能不能命中原文。
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
                    {activeKb ? (
                        <>
                            <Alert
                                type="info"
                                showIcon
                                className="kb-workbench__tip"
                                message={`当前知识库：${activeKb.name}`}
                                description="AskPage 也可以选择这个知识库提问；这里主要用于检查文档是否真的完成入库、检索、重排序和引用。"
                            />
                            <Space wrap style={{ marginTop: 12 }}>
                                <Tag color="geekblue">Embedding：{activeKb.embedding_model}</Tag>
                                <Tag>分块 {activeKb.chunk_size} / overlap {activeKb.chunk_overlap}</Tag>
                                <Tag>召回 topK {activeKb.retrieval_top_k}</Tag>
                                <Tag>重排 topN {activeKb.rerank_top_n}</Tag>
                            </Space>
                        </>
                    ) : null}
                </Card>

                <Card title="文档导入与处理流程" extra={loading ? <Spin size="small" /> : null}>
                    <Alert
                        type="info"
                        showIcon
                        className="kb-workbench__flow"
                        message="三个按钮的意思"
                        description="解析文档：读取正文；生成片段：切成可检索小段；写入向量库：把片段写入 Milvus。只有完成写入向量库，下面的检索和 Test QA 才可能命中。"
                    />
                    <Space wrap style={{ marginBottom: 16 }}>
                        <Upload
                            showUploadList={false}
                            beforeUpload={(file) => {
                                void handleUploadToKb(file);
                                return false;
                            }}
                        >
                            <Button icon={<CloudUploadOutlined />} loading={Boolean(runningStage?.startsWith("upload:"))}>
                                直接上传到当前知识库
                            </Button>
                        </Upload>
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
                    <Typography.Paragraph type="secondary">
                        推荐验收路径：直接上传报告文件到 KB，然后依次点击“解析文档、生成片段、写入向量库”。旧的“导入知识条目”只保留兼容。
                    </Typography.Paragraph>
                    {documents.length ? (
                        <List
                            dataSource={documents}
                            renderItem={(doc) => (
                                <List.Item
                                    className={doc.doc_id === activeDocId ? "kb-document-item kb-document-item--active" : "kb-document-item"}
                                    actions={[
                                        <Button
                                            size="small"
                                            icon={stageMeta.parse.icon}
                                            loading={runningStage === `${doc.doc_id}:parse`}
                                            onClick={() => runDocStage(doc, "parse")}
                                        >
                                            {stageMeta.parse.label}
                                        </Button>,
                                        <Button
                                            size="small"
                                            icon={stageMeta.chunk.icon}
                                            loading={runningStage === `${doc.doc_id}:chunk`}
                                            disabled={!canRunChunk(doc)}
                                            onClick={() => runDocStage(doc, "chunk")}
                                        >
                                            {stageMeta.chunk.label}
                                        </Button>,
                                        <Button
                                            size="small"
                                            type="primary"
                                            icon={stageMeta.index.icon}
                                            loading={runningStage === `${doc.doc_id}:index`}
                                            disabled={!canRunIndex(doc)}
                                            onClick={() => runDocStage(doc, "index")}
                                        >
                                            {stageMeta.index.label}
                                        </Button>,
                                        <Button size="small" onClick={() => handleLoadChunks(doc)}>查看片段</Button>,
                                    ]}
                                >
                                    <List.Item.Meta
                                        avatar={<FileSearchOutlined />}
                                        title={<Space wrap>{doc.title}<StatusTag status={doc.status} /></Space>}
                                        description={<DocumentStatusSummary doc={doc} />}
                                    />
                                </List.Item>
                            )}
                        />
                    ) : <Empty description="暂无文档。先选择一个上传文件或知识条目，导入到当前知识库。" />}
                </Card>

                <Card title="片段预览">
                    <Typography.Paragraph type="secondary">
                        片段是 RAG 真正检索的最小单位。Test QA 命中的不是整份文件，而是这些片段。
                    </Typography.Paragraph>
                    {activeDoc ? <Tag color="blue">当前文档：{activeDoc.title}</Tag> : null}
                    {chunks.length ? (
                        <List
                            dataSource={chunks.slice(0, 8)}
                            renderItem={(chunk) => (
                                <List.Item>
                                    <Typography.Paragraph ellipsis={{ rows: 3, expandable: "collapsible", symbol: "展开" }}>
                                        <Typography.Text type="secondary">片段 #{chunk.chunk_index} · {statusLabel(chunk.vector_status)}</Typography.Text>
                                        <br />
                                        {chunk.text}
                                    </Typography.Paragraph>
                                </List.Item>
                            )}
                        />
                    ) : <Empty description="选择文档并完成“生成片段”后，这里会显示可检索片段。" />}
                </Card>

                <Card title={<Space><ApiOutlined />检索问答测试与 RAG Trace</Space>}>
                    <Alert
                        type="warning"
                        showIcon
                        className="kb-workbench__flow"
                        message="Test QA 是 RAG 链路验收，不是普通聊天页"
                        description="它会调用 /api/v1/rag/test-qa：先检索当前知识库，再基于命中的片段生成可追溯回答。真正的大模型对话请点击“去 AskPage 用大模型问”，AskPage 会带上当前知识库和问题。"
                    />
                    <Space.Compact style={{ width: "100%" }}>
                        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="输入一个能在文档中找到依据的问题" />
                        <Button icon={<SearchOutlined />} onClick={handleSearch} loading={loading}>只测检索</Button>
                        <Button icon={<PlayCircleOutlined />} type="primary" onClick={handleTestQA} loading={loading}>生成测试回答</Button>
                        <Button onClick={handleEval} loading={loading}>运行验收评分</Button>
                        <Button onClick={openAskPageWithCurrentKb}>去 AskPage 用大模型问</Button>
                    </Space.Compact>
                    {searchResult ? <TracePanel mode="search" hits={searchResult.hits} trace={searchResult.trace} /> : null}
                    {qaResult ? (
                        <Card size="small" title="测试回答" style={{ marginTop: 12 }}>
                            <Space wrap style={{ marginBottom: 10 }}>
                                <Tag color={qaModeColor(qaResult.answer_mode)}>{qaModeLabel(qaResult.answer_mode)}</Tag>
                                <Tag color={qaResult.provider_name ? "green" : "default"}>
                                    {qaResult.provider_name ? `大模型：${qaResult.provider_name}` : "未调用大模型"}
                                </Tag>
                                {qaResult.model_name ? <Tag>{qaResult.model_name}</Tag> : null}
                                <Tag color={evidenceQualityColor(qaResult.evidence_quality)}>
                                    证据质量：{evidenceQualityLabel(qaResult.evidence_quality)}
                                </Tag>
                                {typeof qaResult.confidence === "number" ? <Tag>可信度 {Math.round(qaResult.confidence * 100)}%</Tag> : null}
                                {qaResult.selected_chunks?.length ? <Tag color="blue">已选引用片段 {qaResult.selected_chunks.length}</Tag> : null}
                            </Space>
                            <Typography.Paragraph>{qaResult.answer}</Typography.Paragraph>
                            <TracePanel mode="qa" hits={qaResult.hits} trace={qaResult.retrieval_trace} />
                        </Card>
                    ) : null}
                    {evalResult ? <EvalPanel evalResult={evalResult} /> : null}
                </Card>
            </Space>
        </div>
    );
}

function DocumentStatusSummary({ doc }: { doc: RagDocument }) {
    const generatedCount = doc.chunk_count ?? 0;
    const indexedCount = doc.indexed_chunk_count ?? 0;
    return (
        <Space direction="vertical" size={6} className="kb-document-status">
            <Typography.Text type="secondary">
                {documentReadableSummary(doc)}
            </Typography.Text>
            <Space wrap>
                <Tag color={statusColor(doc.parse_status)}>解析：{statusLabel(doc.parse_status)}</Tag>
                <Tag color={statusColor(doc.chunk_status)}>分块：{statusLabel(doc.chunk_status)}</Tag>
                <Tag color={statusColor(doc.index_status)}>向量入库：{statusLabel(doc.index_status)}</Tag>
                <Tag>{vectorBackendLabel(doc.vector_backend)}</Tag>
                <Tag>片段 {generatedCount} 个，已入库 {indexedCount} 个</Tag>
                {doc.source_type ? <Tag>{sourceTypeLabelMap[doc.source_type] ?? doc.source_type}</Tag> : null}
            </Space>
            {doc.index_warnings?.length ? (
                <Alert type="warning" showIcon message={doc.index_warnings.map(humanizeWarning).join("；")} />
            ) : null}
            <Space wrap>
                <Progress size="small" percent={doc.parse_progress ?? parseProgressFromStatus(doc.parse_status)} style={{ width: 160 }} />
                <Typography.Text type="secondary">解析进度</Typography.Text>
                <Progress size="small" percent={doc.chunk_progress ?? chunkProgressFromStatus(doc.chunk_status)} style={{ width: 160 }} />
                <Typography.Text type="secondary">分块进度</Typography.Text>
            </Space>
        </Space>
    );
}

function StatusTag({ status }: { status: string }) {
    return <Tag color={statusColor(status)}>{statusLabel(status)}</Tag>;
}

function TracePanel({ hits, trace, mode }: { hits: RagHit[]; trace: RagSearchResult["trace"]; mode: "search" | "qa" }) {
    const noHits = hits.length === 0;
    return (
        <Space direction="vertical" size={10} style={{ width: "100%", marginTop: 12 }}>
            <Space wrap>
                <Tag color={trace.degraded ? "orange" : "green"}>向量库：{vectorBackendLabel(trace.vector_runtime ?? trace.vector_backend)}</Tag>
                <Tag color={trace.dense_count > 0 ? "geekblue" : "default"}>向量命中 {trace.dense_count}</Tag>
                <Tag color={trace.sparse_count > 0 ? "blue" : "default"}>关键词命中 {trace.sparse_count}</Tag>
                <Tag color={trace.merged_count > 0 ? "cyan" : "default"}>融合候选 {trace.merged_count}</Tag>
                <Tag color={trace.rerank_applied ? "green" : "default"}>重排序：{trace.rerank_applied ? "已执行" : "未执行"}</Tag>
            </Space>
            {trace.warnings?.length ? <Alert type="warning" showIcon message={trace.warnings.map(humanizeWarning).join("；")} /> : null}
            {noHits ? (
                <Empty
                    description={
                        mode === "search"
                            ? "没有检索到片段。请先确认文档已完成“写入向量库”，或换一个更贴近文档原文的问题。"
                            : "没有可引用片段，因此不会生成没有依据的 RAG 回答。"
                    }
                />
            ) : (
                <List
                    size="small"
                    dataSource={hits}
                    renderItem={(hit) => (
                        <List.Item>
                            <List.Item.Meta
                                title={<Space wrap>{hit.title}<Tag>{sourceTypeLabelMap[hit.source_type] ?? hit.source_type}</Tag>{hit.page_number ? <Tag>第 {hit.page_number} 页</Tag> : null}</Space>}
                                description={
                                    <Typography.Paragraph ellipsis={{ rows: 2, expandable: "collapsible", symbol: "展开" }}>
                                        {hit.snippet}
                                    </Typography.Paragraph>
                                }
                            />
                            <Typography.Text type="secondary" className="kb-hit-score">
                                向量 {formatScore(hit.dense_score)} · 关键词 {formatScore(hit.sparse_score)} · 融合 {formatScore(hit.rrf_score)} · 重排 {formatScore(hit.rerank_score)}
                            </Typography.Text>
                        </List.Item>
                    )}
                />
            )}
        </Space>
    );
}

function EvalPanel({ evalResult }: { evalResult: RagEvalRun }) {
    const metrics = evalResult.metrics;
    return (
        <Card size="small" title="验收评分" style={{ marginTop: 12 }}>
            <Space wrap>
                <Tag color={evalResult.passed ? "green" : "red"}>{evalResult.passed ? "通过" : "未通过"}</Tag>
                <Tag>Hit@3 {formatPercent(metrics.hit_at_3)}</Tag>
                <Tag>MRR {formatPercent(metrics.mrr)}</Tag>
                <Tag>引用覆盖 {formatPercent(metrics.citation_coverage)}</Tag>
                <Tag>跨库泄漏 {String(metrics.cross_kb_leak_count ?? 0)}</Tag>
                <Tag>向量失败 {String(metrics.vector_failure_count ?? 0)}</Tag>
            </Space>
            <Typography.Paragraph type="secondary" style={{ marginTop: 8 }}>
                通过线：Milvus Standalone、无降级、Hit@3 ≥ 85%、MRR ≥ 75%、引用覆盖 100%、跨库泄漏 0。
            </Typography.Paragraph>
        </Card>
    );
}

function canRunChunk(doc: RagDocument) {
    return ["parsed", "chunked", "indexed"].includes(doc.parse_status) || doc.chunk_count > 0;
}

function canRunIndex(doc: RagDocument) {
    return ["chunked", "indexed"].includes(doc.chunk_status) || doc.chunk_count > 0;
}

function parseProgressFromStatus(status?: string | null) {
    if (status === "parsed" || status === "indexed" || status === "chunked") return 100;
    if (status === "failed" || status === "parse_failed") return 0;
    return 0;
}

function chunkProgressFromStatus(status?: string | null) {
    if (status === "chunked" || status === "indexed") return 100;
    if (status === "failed" || status === "chunk_failed") return 0;
    return 0;
}

function documentReadableSummary(doc: RagDocument) {
    if (doc.status === "indexed" || doc.index_status === "indexed") {
        return "这份文档已写入向量库，可以被检索和 Test QA 命中。";
    }
    if (doc.chunk_status === "chunked" || doc.chunk_count > 0) {
        return "这份文档已经生成片段，下一步点击“写入向量库”。";
    }
    if (doc.parse_status === "parsed") {
        return "这份文档已经解析出正文，下一步点击“生成片段”。";
    }
    if (doc.status === "failed" || doc.parse_status.includes("failed") || doc.index_status.includes("failed")) {
        return doc.error_message ? `处理失败：${doc.error_message}` : "处理失败，请查看后端日志或重新导入。";
    }
    return "这份文档已导入，下一步点击“解析文档”。";
}

function statusLabel(status?: string | null) {
    if (!status) {
        return "未开始";
    }
    return statusLabelMap[status] ?? status;
}

function statusColor(status?: string | null) {
    if (!status) {
        return "default";
    }
    if (["indexed", "parsed", "chunked"].includes(status)) {
        return "green";
    }
    if (["failed", "parse_failed", "chunk_failed", "index_failed"].includes(status)) {
        return "red";
    }
    if (["running", "parsing", "queued"].includes(status)) {
        return "blue";
    }
    return "default";
}

function vectorBackendLabel(value?: string | null) {
    if (!value) {
        return "向量库：未写入";
    }
    const normalized = value.toLowerCase();
    if (normalized.includes("milvus_standalone") || normalized === "milvus") {
        return "Milvus Docker";
    }
    if (normalized.includes("milvus_lite")) {
        return "Milvus Lite";
    }
    if (normalized.includes("memory")) {
        return "内存开发模式";
    }
    if (normalized.includes("chroma")) {
        return "Chroma 兼容模式";
    }
    return value;
}

function qaModeLabel(value?: string | null) {
    if (value === "llm_grounded") {
        return "已调用大模型生成";
    }
    if (value === "retrieval_only") {
        return "仅检索，生成失败";
    }
    if (value === "no_hits") {
        return "无命中，未调用模型";
    }
    return "Test QA";
}

function qaModeColor(value?: string | null) {
    if (value === "llm_grounded") {
        return "green";
    }
    if (value === "retrieval_only") {
        return "orange";
    }
    if (value === "no_hits") {
        return "red";
    }
    return "default";
}

function evidenceQualityLabel(value?: string | null) {
    if (value === "strong") {
        return "强";
    }
    if (value === "usable") {
        return "可用";
    }
    if (value === "weak") {
        return "弱";
    }
    if (value === "none") {
        return "无";
    }
    return value || "未知";
}

function evidenceQualityColor(value?: string | null) {
    if (value === "strong") {
        return "green";
    }
    if (value === "usable") {
        return "blue";
    }
    if (value === "weak") {
        return "orange";
    }
    if (value === "none") {
        return "red";
    }
    return "default";
}

function humanizeWarning(value: string) {
    if (value.includes("BGE reranker local model is missing")) {
        const target = value.split("pre-download to ")[1];
        return target
            ? `BGE 重排序模型缺失；请先下载或解压到 ${target}`
            : "BGE 重排序模型缺失；请先下载或解压本地 reranker 模型。";
    }
    return value
        .replace(/no_hits/g, "没有命中片段")
        .replace(/rerank_disabled/g, "重排序已禁用")
        .replace(/bge_reranker_unavailable/g, "BGE 重排序不可用")
        .replace(/vector unavailable/g, "向量检索不可用")
        .replace(/fallback/g, "降级")
        .replace(/BGE/g, "BGE")
        .replace(/Milvus/g, "Milvus");
}

function formatScore(value?: number | null) {
    return typeof value === "number" ? value.toFixed(3) : "-";
}

function formatPercent(value: unknown) {
    return typeof value === "number" ? `${Math.round(value * 100)}%` : "-";
}
