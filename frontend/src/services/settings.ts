import { httpClient } from "./http";
import type {
    ModelDiscoveryResult,
    ProviderConnectionRequest,
    ProviderConnectionResult,
    ProviderListResponse,
    ProviderProfile,
    UpdateUserSettingsRequest,
    UpsertProviderProfileRequest,
    UserSettingsEnvelope,
} from "../types/settings";

export async function getSettings() {
    const response = await httpClient.get<UserSettingsEnvelope>("/v1/settings");
    return response.data;
}

export async function patchSettings(payload: UpdateUserSettingsRequest) {
    const response = await httpClient.patch<UserSettingsEnvelope>("/v1/settings", payload);
    return response.data;
}

export async function listProviderProfiles() {
    const response = await httpClient.get<ProviderListResponse>("/v1/settings/providers");
    return response.data;
}

export async function createProviderProfile(payload: UpsertProviderProfileRequest) {
    const response = await httpClient.post<ProviderProfile>("/v1/settings/providers", payload);
    return response.data;
}

export async function updateProviderProfile(profileId: string, payload: UpsertProviderProfileRequest) {
    const response = await httpClient.patch<ProviderProfile>(`/v1/settings/providers/${profileId}`, payload);
    return response.data;
}

export async function deleteProviderProfile(profileId: string) {
    const response = await httpClient.delete<{ status: string }>(`/v1/settings/providers/${profileId}`);
    return response.data;
}

export async function testProviderConnection(payload: ProviderConnectionRequest) {
    const response = await httpClient.post<ProviderConnectionResult>("/v1/settings/providers/test", payload);
    return response.data;
}

export async function discoverProviderModels(payload: ProviderConnectionRequest) {
    const response = await httpClient.post<ModelDiscoveryResult>("/v1/settings/providers/discover-models", payload);
    return response.data;
}
