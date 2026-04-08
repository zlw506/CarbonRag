import axios from "axios";
import type { FeedbackRequest, FeedbackResponse } from "../types/feedback";
import { httpClient } from "./http";

export async function submitFeedback(payload: FeedbackRequest) {
    try {
        const response = await httpClient.post<FeedbackResponse>("/api/v1/feedback", payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}
