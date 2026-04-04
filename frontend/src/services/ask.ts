import axios from "axios";
import { httpClient } from "./http";
import type { AskRequest, AskResponse } from "../types/ask";

export async function submitAskRequest(payload: AskRequest) {
    try {
        const response = await httpClient.post<AskResponse>("/api/v1/ask", payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError<AskResponse>(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}
