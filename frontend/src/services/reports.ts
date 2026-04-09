import axios from "axios";
import { httpClient } from "./http";
import type {
    CreateReportRequest,
    ReportDetail,
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
