function normalizeApiBaseUrl(rawValue?: string) {
    const fallback = "http://127.0.0.1:8000/api";

    if (!rawValue || !rawValue.trim()) {
        return fallback;
    }

    const trimmedValue = rawValue.trim().replace(/\/+$/, "");

    if (trimmedValue === "/api") {
        return trimmedValue;
    }

    try {
        const parsedUrl = new URL(trimmedValue);
        const normalizedPath = parsedUrl.pathname.replace(/\/+$/, "");

        if (!normalizedPath) {
            parsedUrl.pathname = "/api";
            return parsedUrl.toString().replace(/\/+$/, "");
        }

        return trimmedValue;
    } catch {
        return trimmedValue;
    }
}

const env = {
    apiBaseUrl: normalizeApiBaseUrl(import.meta.env.VITE_API_BASE_URL),
    appTitle: import.meta.env.VITE_APP_TITLE ?? "CarbonRag 对话工作台"
};

export default env;
