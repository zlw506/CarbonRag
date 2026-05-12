import { httpClient } from "./http";
import type { RagRetrievalResult, RagRetrieveRequest } from "../types/rag";
import type { RagEvalRun, RagSearchResult, RagTestQAResult, RagRetrievalMode } from "../types/kb";

export async function retrieveRagEvidence(payload: RagRetrieveRequest) {
    const response = await httpClient.post<RagRetrievalResult>("/v1/rag/retrieve", payload);
    return response.data;
}

export async function searchRagSpine(payload: {
    query: string;
    kb_id?: string | null;
    mode?: RagRetrievalMode;
    top_k?: number;
    knowledge_scope?: "public" | "private_sample" | "mixed";
}) {
    const response = await httpClient.post<RagSearchResult>("/v1/rag/search", {
        knowledge_scope: "mixed",
        mode: "hybrid_rerank",
        top_k: 5,
        ...payload,
    });
    return response.data;
}

export async function runRagTestQA(payload: {
    query: string;
    kb_id?: string | null;
    mode?: RagRetrievalMode;
    top_k?: number;
    knowledge_scope?: "public" | "private_sample" | "mixed";
}) {
    const response = await httpClient.post<RagTestQAResult>("/v1/rag/test-qa", {
        knowledge_scope: "mixed",
        mode: "hybrid_rerank",
        top_k: 5,
        ...payload,
    });
    return response.data;
}

export async function runRagEval(payload: {
    kb_id?: string | null;
    mode?: RagRetrievalMode;
    top_k?: number;
}) {
    const response = await httpClient.post<RagEvalRun>("/v1/rag/eval/run", {
        mode: "hybrid_rerank",
        top_k: 5,
        ...payload,
    });
    return response.data;
}
