import type { CarbonCalculationSummary } from "./carbon";
import type { LocalProviderOverride } from "./settings";

export type ReportType = "policy_summary" | "mixed_analysis" | "carbon_summary";
export type ReportCitationSourceType =
    | "public_policy"
    | "public_policy_demo"
    | "private_sample"
    | "private_upload"
    | "carbon_factor";
export type ReportSourceType = "message" | "citation" | "carbon_result";

export interface ReportCitation {
    source_type: ReportCitationSourceType;
    title: string;
    source: string;
    source_url: string | null;
    snippet: string;
    chunk_id: string | null;
    factor_id: string | null;
}

export interface ReportSourceSummary {
    public_policy_count: number;
    public_policy_demo_count?: number;
    private_sample_count: number;
    private_upload_count?: number;
    carbon_factor_count: number;
    total_citation_count: number;
}

export interface ReportSourceEntry {
    source_type: ReportSourceType;
    source_ref: string;
    label: string;
    order_index: number;
}

export interface ReportSummary {
    report_id: string;
    report_type: ReportType;
    title: string;
    created_at: string;
    updated_at: string;
    source_count: number;
}

export interface ReportDetail {
    report_id: string;
    session_id: string;
    report_type: ReportType;
    title: string;
    status: "ok";
    content: string;
    output_format: "markdown";
    citations: ReportCitation[];
    source_summary: ReportSourceSummary;
    sources: ReportSourceEntry[];
    trace_id: string;
    created_at: string;
    updated_at: string;
}

export interface CreateReportRequest {
    session_id: string;
    report_type: ReportType;
    title?: string;
    source_message_ids?: string[];
    carbon_result_id?: string;
    output_format?: "markdown";
    request_group_id?: string;
    resume_cursor?: number;
    provider_override?: LocalProviderOverride;
}

export interface UpdateReportRequest {
    title?: string;
    content: string;
}

export type ReportExportFormat = "docx" | "pdf";

export interface CreateReportExportRequest {
    formats: ReportExportFormat[];
    template_id?: string;
    include_citations?: boolean;
    include_source_snippets?: boolean;
    include_carbon_trace?: boolean;
    force_regenerate?: boolean;
}

export interface ReportFileSummary {
    file_id: string;
    format: ReportExportFormat;
    filename: string;
    download_url: string;
    content_type: string;
    file_size_bytes: number;
    checksum_sha256: string;
    created_at: string;
}

export interface ReportExportResponse {
    report_id: string;
    files: ReportFileSummary[];
}

export type SessionCarbonCalculationSummary = CarbonCalculationSummary;
