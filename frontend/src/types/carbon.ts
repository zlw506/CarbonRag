export type CarbonActivityItem = "electricity" | "natural_gas" | "diesel";

export interface CalcCarbonRequest {
    session_id?: string;
    period_label?: string;
    electricity_kwh?: number;
    natural_gas_m3?: number;
    diesel_l?: number;
}

export interface CarbonBreakdownItem {
    item: CarbonActivityItem;
    activity_value: number;
    activity_unit: string;
    factor_value: number;
    factor_unit: string;
    emission_kgco2e: number;
    factor_id: string;
}

export interface CarbonCitation {
    factor_id: string;
    source: string;
    source_url: string;
}

export interface CalcCarbonResponse {
    status: "ok";
    trace_id: string;
    total_emission_kgco2e: number;
    breakdown: CarbonBreakdownItem[];
    formula_summary: string;
    citations: CarbonCitation[];
}

export interface CarbonCalculationSummary {
    trace_id: string;
    period_label?: string | null;
    total_emission_kgco2e: number;
    created_at: string;
}
