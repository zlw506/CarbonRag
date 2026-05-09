export type CarbonActivityItem = string;

export interface CalcCarbonRequest {
    session_id?: string;
    period_label?: string;
    organization_id?: string;
    facility_id?: string;
    period_start?: string;
    period_end?: string;
    inventory_standard?: string;
    activity_items?: CarbonActivityInput[];
    electricity_kwh?: number;
    natural_gas_m3?: number;
    diesel_l?: number;
}

export interface CarbonActivityInput {
    scope: "scope1" | "scope2" | "scope3";
    activity_category: string;
    activity_name: string;
    activity_value: number;
    activity_unit: string;
    region?: string | null;
    year?: number | null;
    factor_preference?: string;
    scope2_method?: string;
    certified_green_kwh?: number | null;
    evidence_reference?: string | null;
    requested_factor_id?: string | null;
    metadata?: Record<string, string>;
}

export interface CarbonBreakdownItem {
    item: CarbonActivityItem;
    scope?: string | null;
    activity_category?: string | null;
    activity_name?: string | null;
    activity_value: number;
    activity_unit: string;
    normalized_activity_value?: number | null;
    normalized_activity_unit?: string | null;
    factor_value: number;
    factor_unit: string;
    emission_kgco2e: number;
    factor_id: string;
}

export interface CarbonCitation {
    factor_id: string;
    source: string;
    source_url?: string | null;
}

export interface CarbonFactorSnapshot {
    factor_id: string;
    factor_version: string;
    source_type: string;
    source_name: string;
    source_url?: string | null;
    scope: string;
    activity_category: string;
    activity_name: string;
    region?: string | null;
    region_name?: string | null;
    year?: number | null;
    factor_value: number;
    factor_unit: string;
    activity_unit: string;
    result_unit: string;
    is_default: boolean;
    is_deprecated: boolean;
    notes?: string | null;
}

export interface CarbonUnitConversionTrace {
    activity_name: string;
    input_value: number;
    input_unit: string;
    normalized_value: number;
    normalized_unit: string;
    conversion_factor: number;
}

export interface CarbonFormulaTrace {
    activity_name: string;
    formula: string;
    normalized_activity_value: number;
    activity_unit: string;
    factor_value: number;
    factor_unit: string;
    emission_kgco2e: number;
}

export interface CarbonSourceSummaryItem {
    source_type: string;
    source_name: string;
    source_url?: string | null;
    factor_count: number;
}

export interface CalcCarbonResponse {
    status: "ok";
    trace_id: string;
    total_emission_kgco2e: number;
    breakdown: CarbonBreakdownItem[];
    formula_summary: string;
    citations: CarbonCitation[];
    factor_snapshot: CarbonFactorSnapshot[];
    unit_conversion_trace: CarbonUnitConversionTrace[];
    formula_trace: CarbonFormulaTrace[];
    source_summary: CarbonSourceSummaryItem[];
    warnings: string[];
}

export interface CarbonCalculationSummary {
    trace_id: string;
    period_label?: string | null;
    total_emission_kgco2e: number;
    created_at: string;
}
