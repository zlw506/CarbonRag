export interface SystemInfo {
    app_name: string;
    version: string;
    env: string;
    api_prefix: string;
    model_provider_mode: string;
    timestamp: string;
}

export interface HealthStatus {
    status: string;
}
