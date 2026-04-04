const env = {
    apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000",
    appTitle: import.meta.env.VITE_APP_TITLE ?? "CarbonRag Public Policy Grounded Ask"
};

export default env;
