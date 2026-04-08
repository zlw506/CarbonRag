import { httpClient } from "./http";
import type { SystemInfo } from "../types/system";


export async function fetchSystemInfo() {
    const response = await httpClient.get<SystemInfo>("/v1/system/info");
    return response.data;
}
