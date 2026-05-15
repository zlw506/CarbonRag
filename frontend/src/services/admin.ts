import { httpClient } from "./http";
import type {
    AdminFeedbackOverview,
    AdminPrivateSampleItem,
    AdminSystemStatus,
    AdminUserSummary,
    DeleteAdminUsersRequest,
    DeleteAdminUsersResponse,
    KnowledgeRefreshTask,
    PolicyCrawlerCandidateStatus,
    PolicyCrawlerCandidateArtifactsSummary,
    PolicyCrawlerCandidateSummary,
    PolicyCrawlerDryRunSummary,
    PolicyCrawlerRecommendedImportSummary,
    PolicyCrawlerRunSummary,
    PolicyCrawlerSourceSummary,
    PolicyCrawlerSourceUpsertRequest,
    PolicyCrawlerStatusSummary,
    PolicyShowcaseChunkSummary,
    PolicyShowcaseRetrievalPreview,
    PolicyShowcaseSourceSummary,
    PolicyShowcaseStatus,
    TriggerKnowledgeRefreshRequest,
    UpdateAdminPrivateSampleRequest,
    UpdateAdminUserRequest,
    ResetPasswordResponse,
} from "../types/admin";

const crawlerRequestConfig = { timeout: 120000 };

export async function listAdminUsers() {
    const response = await httpClient.get<AdminUserSummary[]>("/v1/admin/users");
    return response.data;
}

export async function updateAdminUser(userId: string, payload: UpdateAdminUserRequest) {
    const response = await httpClient.patch<AdminUserSummary>(`/v1/admin/users/${userId}`, payload);
    return response.data;
}

export async function resetAdminUserPassword(userId: string) {
    const response = await httpClient.post<ResetPasswordResponse>(`/v1/admin/users/${userId}/reset-password`);
    return response.data;
}

export async function deleteAdminUsers(payload: DeleteAdminUsersRequest) {
    const response = await httpClient.delete<DeleteAdminUsersResponse>("/v1/admin/users", { data: payload });
    return response.data;
}

export async function getAdminFeedbackOverview() {
    const response = await httpClient.get<AdminFeedbackOverview>("/v1/admin/feedback/overview");
    return response.data;
}

export async function listAdminPrivateSamples() {
    const response = await httpClient.get<AdminPrivateSampleItem[]>("/v1/admin/private-samples");
    return response.data;
}

export async function listPolicyShowcaseSources() {
    const response = await httpClient.get<PolicyShowcaseSourceSummary[]>("/v1/admin/policy-sources");
    return response.data;
}

export async function runPolicyShowcaseSource(sourceId: string) {
    const response = await httpClient.post<PolicyShowcaseStatus>(`/v1/admin/policy-sources/${sourceId}/run`, {});
    return response.data;
}

export async function getPolicyShowcaseStatus(sourceId: string) {
    const response = await httpClient.get<PolicyShowcaseStatus>(`/v1/admin/policy-sources/${sourceId}/status`);
    return response.data;
}

export async function listPolicyShowcaseChunks(sourceId: string) {
    const response = await httpClient.get<PolicyShowcaseChunkSummary[]>(`/v1/admin/policy-sources/${sourceId}/chunks`);
    return response.data;
}

export async function getPolicyShowcaseRetrievalPreview(sourceId: string, query?: string, topK = 5) {
    const response = await httpClient.get<PolicyShowcaseRetrievalPreview>(
        `/v1/admin/policy-sources/${sourceId}/retrieval-preview`,
        {
            params: {
                query,
                top_k: topK,
            },
        },
    );
    return response.data;
}

export async function getPolicyCrawlerStatus() {
    const response = await httpClient.get<PolicyCrawlerStatusSummary>("/v1/admin/policy-crawler/status");
    return response.data;
}

export async function listPolicyCrawlerSources() {
    const response = await httpClient.get<PolicyCrawlerSourceSummary[]>("/v1/admin/policy-crawler/sources");
    return response.data;
}

export async function createPolicyCrawlerSource(payload: PolicyCrawlerSourceUpsertRequest) {
    const response = await httpClient.post<PolicyCrawlerSourceSummary>("/v1/admin/policy-crawler/sources", payload);
    return response.data;
}

export async function updatePolicyCrawlerSource(sourceId: string, payload: PolicyCrawlerSourceUpsertRequest) {
    const response = await httpClient.patch<PolicyCrawlerSourceSummary>(
        `/v1/admin/policy-crawler/sources/${sourceId}`,
        payload,
    );
    return response.data;
}

export async function deletePolicyCrawlerSource(sourceId: string) {
    const response = await httpClient.delete<{ status: string; source_id: string }>(
        `/v1/admin/policy-crawler/sources/${sourceId}`,
    );
    return response.data;
}

export async function importRecommendedPolicyCrawlerSources() {
    const response = await httpClient.post<PolicyCrawlerRecommendedImportSummary>(
        "/v1/admin/policy-crawler/sources/recommended/import",
        {},
    );
    return response.data;
}

export async function dryRunPolicyCrawlerSource(sourceId: string) {
    const response = await httpClient.post<PolicyCrawlerDryRunSummary>(
        `/v1/admin/policy-crawler/sources/${sourceId}/dry-run`,
        {},
        crawlerRequestConfig,
    );
    return response.data;
}

export async function runPolicyCrawlerSource(sourceId: string) {
    const response = await httpClient.post<PolicyCrawlerRunSummary>(
        `/v1/admin/policy-crawler/sources/${sourceId}/run`,
        {},
        crawlerRequestConfig,
    );
    return response.data;
}

export async function listPolicyCrawlerRuns(sourceId?: string, limit = 20) {
    const response = await httpClient.get<PolicyCrawlerRunSummary[]>("/v1/admin/policy-crawler/runs", {
        params: {
            source_id: sourceId,
            limit,
        },
    });
    return response.data;
}

export async function listPolicyCrawlerCandidates(
    status?: PolicyCrawlerCandidateStatus,
    sourceId?: string,
    limit = 50,
) {
    const response = await httpClient.get<PolicyCrawlerCandidateSummary[]>("/v1/admin/policy-crawler/candidates", {
        params: {
            status,
            source_id: sourceId,
            limit,
        },
    });
    return response.data;
}

export async function publishPolicyCrawlerCandidate(candidateId: string) {
    const response = await httpClient.post<PolicyCrawlerCandidateSummary>(
        `/v1/admin/policy-crawler/candidates/${candidateId}/publish`,
        {},
    );
    return response.data;
}

export async function publishPolicyCrawlerCandidateToRag(candidateId: string) {
    const response = await httpClient.post<PolicyCrawlerCandidateSummary>(
        `/v1/admin/policy-crawler/candidates/${candidateId}/publish-to-rag`,
        {},
        crawlerRequestConfig,
    );
    return response.data;
}

export async function getPolicyCrawlerCandidateArtifacts(candidateId: string) {
    const response = await httpClient.get<PolicyCrawlerCandidateArtifactsSummary>(
        `/v1/admin/policy-crawler/candidates/${candidateId}/artifacts`,
        crawlerRequestConfig,
    );
    return response.data;
}

export async function rejectPolicyCrawlerCandidate(candidateId: string) {
    const response = await httpClient.post<PolicyCrawlerCandidateSummary>(
        `/v1/admin/policy-crawler/candidates/${candidateId}/reject`,
        {},
    );
    return response.data;
}

export async function updateAdminPrivateSample(docId: string, payload: UpdateAdminPrivateSampleRequest) {
    const response = await httpClient.patch<AdminPrivateSampleItem>(`/v1/admin/private-samples/${docId}`, payload);
    return response.data;
}

export async function listKnowledgeRefreshTasks() {
    const response = await httpClient.get<KnowledgeRefreshTask[]>("/v1/admin/knowledge-refresh-tasks");
    return response.data;
}

export async function triggerKnowledgeRefresh(payload: TriggerKnowledgeRefreshRequest) {
    const response = await httpClient.post<KnowledgeRefreshTask>("/v1/admin/knowledge-refresh-tasks", payload);
    return response.data;
}

export async function getAdminSystemStatus() {
    const response = await httpClient.get<AdminSystemStatus>("/v1/admin/system/status");
    return response.data;
}
