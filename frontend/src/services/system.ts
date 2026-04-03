import { httpClient } from "./http";
import type { HealthStatus, SystemInfo } from "../types/system";

export async function fetchSystemInfo() {
    const response = await httpClient.get<SystemInfo>("/api/v1/system/info");
    return response.data;
}

export async function fetchHealthStatus() {
    const response = await httpClient.get<HealthStatus>("/healthz");
    return response.data;
}
