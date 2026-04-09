import { httpClient } from "./http";
import type {
    AdminFeedbackOverview,
    AdminPrivateSampleItem,
    AdminSystemStatus,
    AdminUserSummary,
    KnowledgeRefreshTask,
    TriggerKnowledgeRefreshRequest,
    UpdateAdminPrivateSampleRequest,
    UpdateAdminUserRequest,
    ResetPasswordResponse,
} from "../types/admin";

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

export async function getAdminFeedbackOverview() {
    const response = await httpClient.get<AdminFeedbackOverview>("/v1/admin/feedback/overview");
    return response.data;
}

export async function listAdminPrivateSamples() {
    const response = await httpClient.get<AdminPrivateSampleItem[]>("/v1/admin/private-samples");
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
