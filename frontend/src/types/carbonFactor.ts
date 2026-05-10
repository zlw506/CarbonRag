export interface CarbonFactorSource {
    source_id: string;
    title: string;
    publisher: string;
    source_url?: string | null;
    license?: string | null;
    published_year?: number | null;
    source_type: string;
    created_at: string;
    updated_at: string;
}

export interface CarbonFactorSummary {
    factor_id: string;
    name: string;
    category: string;
    industry?: string | null;
    scope: string;
    region?: string | null;
    region_code?: string | null;
    region_name?: string | null;
    year?: number | null;
    factor_value: number;
    factor_unit: string;
    activity_unit: string;
    co2e_unit: string;
    quality: string;
    version: string;
    source?: CarbonFactorSource | null;
    tags: string[];
}

export interface CarbonFactorDetail extends CarbonFactorSummary {
    aliases: string[];
    metadata: Record<string, unknown>;
    is_enabled: boolean;
    created_at: string;
    updated_at: string;
}

export interface CarbonFactorSearchResponse {
    items: CarbonFactorSummary[];
    total: number;
    page: number;
    page_size: number;
}

export interface CarbonFactorCatalogEntry {
    entry_id: string;
    name: string;
    category: string;
    industry?: string | null;
    region?: string | null;
    year?: number | null;
    factor_unit?: string | null;
    activity_unit?: string | null;
    value_status: "calculation_ready" | "encrypted" | string;
    raw_value?: string | null;
    factor_value?: number | null;
    is_calculation_ready: boolean;
    source_title?: string | null;
    publisher?: string | null;
    source_url?: string | null;
    metadata: Record<string, unknown>;
}

export interface CarbonFactorCatalogSearchResponse {
    items: CarbonFactorCatalogEntry[];
    total: number;
    page: number;
    page_size: number;
}

export interface CarbonFactorCategoryNode {
    label: string;
    value?: string | null;
    count?: number;
    children: Array<{
        label: string;
        value?: string | null;
        count: number;
        raw_count?: number;
    }>;
}

export interface CarbonFactorFacets {
    categories: string[];
    industries: string[];
    regions: string[];
    years: number[];
    source_types: string[];
    qualities: string[];
    category_tree: CarbonFactorCategoryNode[];
}

export interface CarbonCalculatorCatalogGroup {
    group_key: string;
    label: string;
    hint: string;
    count: number;
}

export interface CarbonCalculatorCatalogItem {
    item_id: string;
    factor_id: string;
    group_key: string;
    group_label: string;
    name: string;
    factor_value: number;
    factor_unit: string;
    activity_unit: string;
    result_unit: string;
    scope: string;
    activity_category: string;
    activity_name: string;
    source_name: string;
    source_url?: string | null;
    tip?: string | null;
    order: number;
}

export interface CarbonCalculatorCatalogResponse {
    groups: CarbonCalculatorCatalogGroup[];
    items: CarbonCalculatorCatalogItem[];
    total: number;
}
