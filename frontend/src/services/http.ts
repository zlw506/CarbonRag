import axios from "axios";
import env from "../app/env";

export const httpClient = axios.create({
    baseURL: env.apiBaseUrl,
    timeout: 30000
});
