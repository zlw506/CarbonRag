import { httpClient } from "./http";
import type { KnowledgeBase, RagChunk, RagDocument } from "../types/kb";

export async function listKnowledgeBases() {
    const response = await httpClient.get<KnowledgeBase[]>("/v1/kb");
    return response.data;
}

export async function createKnowledgeBase(payload: { name: string; description?: string }) {
    const response = await httpClient.post<KnowledgeBase>("/v1/kb", payload);
    return response.data;
}

export async function createKbDocument(kbId: string, payload: { knowledge_item_id?: string; title?: string; text?: string }) {
    const response = await httpClient.post<RagDocument>(`/v1/kb/${encodeURIComponent(kbId)}/documents`, payload);
    return response.data;
}

export async function listKbDocuments(kbId: string) {
    const response = await httpClient.get<RagDocument[]>(`/v1/kb/${encodeURIComponent(kbId)}/documents`);
    return response.data;
}

export async function parseKbDocument(kbId: string, docId: string) {
    const response = await httpClient.post<RagDocument>(`/v1/kb/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(docId)}/parse`);
    return response.data;
}

export async function chunkKbDocument(kbId: string, docId: string) {
    const response = await httpClient.post<RagDocument>(`/v1/kb/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(docId)}/chunk`);
    return response.data;
}

export async function indexKbDocument(kbId: string, docId: string) {
    const response = await httpClient.post<RagDocument>(`/v1/kb/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(docId)}/index`);
    return response.data;
}

export async function listKbDocumentChunks(kbId: string, docId: string) {
    const response = await httpClient.get<RagChunk[]>(`/v1/kb/${encodeURIComponent(kbId)}/documents/${encodeURIComponent(docId)}/chunks`);
    return response.data;
}

