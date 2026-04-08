import axios from "axios";
import type { CalcCarbonRequest, CalcCarbonResponse } from "../types/carbon";
import { httpClient } from "./http";

export async function submitCarbonCalculation(payload: CalcCarbonRequest) {
    try {
        const response = await httpClient.post<CalcCarbonResponse>("/v1/calc-carbon", payload);
        return response.data;
    } catch (error) {
        if (axios.isAxiosError(error) && error.response?.data) {
            throw error.response.data;
        }
        throw error;
    }
}
