import { httpClient } from "./http";
import type { PrivateSampleCatalogItem } from "../types/privateSample";

export async function listPrivateSamples() {
    const response = await httpClient.get<PrivateSampleCatalogItem[]>("/v1/private-samples");
    return response.data;
}
