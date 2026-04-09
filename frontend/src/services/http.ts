import axios from "axios";
import env from "../app/env";

export const httpClient = axios.create({
    baseURL: env.apiBaseUrl,
    timeout: 30000,
    withCredentials: true,
});

httpClient.interceptors.response.use(
    (response) => response,
    (error) => {
        const requestUrl = error?.config?.url ?? "";
        const isAuthEndpoint = typeof requestUrl === "string" && requestUrl.startsWith("/v1/auth/");
        if (axios.isAxiosError(error) && error.response?.status === 401 && !isAuthEndpoint) {
            window.location.replace("/login");
        }
        return Promise.reject(error);
    },
);
