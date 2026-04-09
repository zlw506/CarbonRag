export type UserRole = "user" | "admin";

export interface AuthUser {
    user_id: string;
    username: string;
    role: UserRole;
    is_active: boolean;
    password_must_change: boolean;
    created_at: string;
    updated_at: string;
    last_login_at: string | null;
}

export interface AuthUserEnvelope {
    user: AuthUser;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface RegisterRequest extends LoginRequest {}

export interface LoginResponse extends AuthUserEnvelope {
    must_change_password: boolean;
}

export interface ChangePasswordRequest {
    current_password: string;
    new_password: string;
}

export interface AuthStatusResponse {
    status: "ok";
}
