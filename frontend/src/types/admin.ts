import type { UserRole } from "./auth";

export interface AdminUserSummary {
    user_id: string;
    username: string;
    role: UserRole;
    is_active: boolean;
    password_must_change: boolean;
    created_at: string;
    last_login_at: string | null;
    session_count: number;
    report_count: number;
    feedback_count: number;
}

export interface UpdateAdminUserRequest {
    role: UserRole;
    is_active: boolean;
}

export interface ResetPasswordResponse {
    status: "ok";
    temporary_password: string;
}

export interface AdminFeedbackRecentEntry {
    feedback_id: string;
    target_type: string;
    rating: string;
    session_id: string | null;
    owner_user_id: string | null;
    created_at: string;
}

export interface AdminFeedbackOverview {
    total_count: number;
    ask_up_count: number;
    ask_down_count: number;
    calc_up_count: number;
    calc_down_count: number;
    recent_entries: AdminFeedbackRecentEntry[];
}

export interface AdminPrivateSampleItem {
    doc_id: string;
    title: string;
    source_type: string;
    sample_type: string;
    business_topic: string;
    session_attachable: boolean;
    is_enabled: boolean;
}

export interface UpdateAdminPrivateSampleRequest {
    is_enabled: boolean;
    session_attachable: boolean;
}

export type KnowledgeRefreshScope = "public_policy" | "private_sample" | "all";
export type KnowledgeRefreshStatus = "running" | "succeeded" | "failed";

export interface KnowledgeRefreshTask {
    task_id: string;
    scope: KnowledgeRefreshScope;
    status: KnowledgeRefreshStatus;
    requested_by_user_id: string | null;
    summary: string | null;
    created_at: string;
    started_at: string | null;
    finished_at: string | null;
}

export interface TriggerKnowledgeRefreshRequest {
    scope: KnowledgeRefreshScope;
}

export interface AdminSystemStatus {
    app_name: string;
    version: string;
    env: string;
    database_backend: string;
    model_provider_mode: string;
    model_name: string;
    total_users: number;
    total_sessions: number;
    total_reports: number;
    total_feedback_entries: number;
    total_private_samples: number;
    enabled_private_samples: number;
    latest_refresh_status: KnowledgeRefreshStatus | null;
}
