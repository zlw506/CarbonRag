import type {
    CarbonCalculatorCatalogResponse,
    CarbonFactorCatalogSearchResponse,
    CarbonFactorDetail,
    CarbonFactorFacets,
    CarbonFactorSearchResponse,
    CarbonFactorSource,
} from "../types/carbonFactor";
import { httpClient } from "./http";

export interface SearchCarbonFactorsParams {
    q?: string;
    category?: string;
    industry?: string;
    region?: string;
    year?: number;
    source_type?: string;
    quality?: string;
    unit?: string;
    page?: number;
    page_size?: number;
}

export interface SearchCarbonFactorCatalogParams {
    q?: string;
    category?: string;
    industry?: string;
    year?: number;
    value_status?: string;
    page?: number;
    page_size?: number;
}

export async function searchCarbonFactors(params: SearchCarbonFactorsParams = {}) {
    const response = await httpClient.get<CarbonFactorSearchResponse>("/v1/carbon-factors", { params });
    return response.data;
}

export async function searchCarbonFactorCatalog(params: SearchCarbonFactorCatalogParams = {}) {
    const response = await httpClient.get<CarbonFactorCatalogSearchResponse>("/v1/carbon-factor-catalog", { params });
    return response.data;
}

export async function getCarbonFactor(factorId: string) {
    const response = await httpClient.get<CarbonFactorDetail>(`/v1/carbon-factors/${encodeURIComponent(factorId)}`);
    return response.data;
}

export async function getCarbonFactorFacets() {
    const response = await httpClient.get<CarbonFactorFacets>("/v1/carbon-factors/facets");
    return response.data;
}

export async function listCarbonFactorSources() {
    const response = await httpClient.get<CarbonFactorSource[]>("/v1/carbon-factor-sources");
    return response.data;
}

export async function getCarbonCalculatorCatalog() {
    const response = await httpClient.get<CarbonCalculatorCatalogResponse>("/v1/carbon-calculator/catalog");
    return response.data;
}
