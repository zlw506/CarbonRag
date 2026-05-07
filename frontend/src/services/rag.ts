import { httpClient } from "./http";
import type { RagRetrievalResult, RagRetrieveRequest } from "../types/rag";

export async function retrieveRagEvidence(payload: RagRetrieveRequest) {
    const response = await httpClient.post<RagRetrievalResult>("/v1/rag/retrieve", payload);
    return response.data;
}
