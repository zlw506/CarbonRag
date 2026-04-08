import axios from "axios";
import { httpClient } from "./http";
import type { UploadedFile } from "../types/session";

export async function uploadSessionFile(sessionId: string, file: File) {
    const formData = new FormData();
    formData.append("session_id", sessionId);
    formData.append("file", file);

    try {
        const response = await httpClient.post<UploadedFile>("/v1/files", formData, {
            headers: {
                "Content-Type": "multipart/form-data",
            },
        });
        return response.data;
    } catch (error) {
        if (axios.isAxiosError<{ detail?: string }>(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}
