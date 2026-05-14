import axios from "axios";
import { httpClient } from "./http";
import type {
    CreateReportRequest,
    CreateReportExportRequest,
    ReportDetail,
    ReportExportResponse,
    ReportFileSummary,
    ReportSummary,
    SessionCarbonCalculationSummary,
    UpdateReportRequest,
} from "../types/report";

export async function listSessionReports(sessionId: string) {
    const response = await httpClient.get<ReportSummary[]>(`/v1/sessions/${sessionId}/reports`);
    return response.data;
}

export async function listSessionCarbonResults(sessionId: string) {
    const response = await httpClient.get<SessionCarbonCalculationSummary[]>(
        `/v1/sessions/${sessionId}/carbon-calculations`,
    );
    return response.data;
}

export async function createReport(payload: CreateReportRequest) {
    try {
        const response = await httpClient.post<ReportDetail>("/v1/reports", payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}

export async function getReport(reportId: string) {
    const response = await httpClient.get<ReportDetail>(`/v1/reports/${reportId}`);
    return response.data;
}

export async function updateReport(reportId: string, payload: UpdateReportRequest) {
    try {
        const response = await httpClient.patch<ReportDetail>(`/v1/reports/${reportId}`, payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}

export async function listReportExports(reportId: string) {
    const response = await httpClient.get<ReportExportResponse>(`/v1/reports/${reportId}/exports`);
    return response.data;
}

export async function createReportExports(reportId: string, payload: CreateReportExportRequest) {
    try {
        const response = await httpClient.post<ReportExportResponse>(`/v1/reports/${reportId}/exports`, payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}

function normalizeDownloadUrl(downloadUrl: string) {
    if (downloadUrl.startsWith("/api/")) {
        return downloadUrl.slice("/api".length);
    }
    return downloadUrl;
}

function parseContentDispositionFilename(contentDisposition: string | undefined) {
    if (!contentDisposition) {
        return null;
    }
    const utf8Match = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
    if (utf8Match?.[1]) {
        return decodeURIComponent(utf8Match[1].trim().replace(/^"|"$/g, ""));
    }
    const asciiMatch = contentDisposition.match(/filename="?([^";]+)"?/i);
    return asciiMatch?.[1]?.trim() || null;
}

export async function downloadReportFile(file: ReportFileSummary) {
    const response = await httpClient.get<Blob>(normalizeDownloadUrl(file.download_url), {
        responseType: "blob",
    });
    return {
        blob: response.data,
        filename: parseContentDispositionFilename(response.headers["content-disposition"]) ?? file.filename,
    };
}
