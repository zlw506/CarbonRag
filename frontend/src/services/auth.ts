import { httpClient } from "./http";
import type {
    AuthStatusResponse,
    AuthUserEnvelope,
    ChangePasswordRequest,
    LoginRequest,
    LoginResponse,
    RegisterRequest,
} from "../types/auth";

export async function registerAccount(payload: RegisterRequest) {
    const response = await httpClient.post<AuthUserEnvelope>("/v1/auth/register", payload);
    return response.data;
}

export async function loginAccount(payload: LoginRequest) {
    const response = await httpClient.post<LoginResponse>("/v1/auth/login", payload);
    return response.data;
}

export async function logoutAccount() {
    const response = await httpClient.post<AuthStatusResponse>("/v1/auth/logout");
    return response.data;
}

export async function getCurrentUser() {
    const response = await httpClient.get<AuthUserEnvelope>("/v1/auth/me");
    return response.data;
}

export async function changePassword(payload: ChangePasswordRequest) {
    const response = await httpClient.post<LoginResponse>("/v1/auth/change-password", payload);
    return response.data;
}
