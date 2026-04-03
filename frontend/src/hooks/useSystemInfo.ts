import { useEffect, useState } from "react";
import { fetchHealthStatus, fetchSystemInfo } from "../services/system";
import type { HealthStatus, SystemInfo } from "../types/system";

interface SystemInfoState {
    info: SystemInfo | null;
    health: HealthStatus | null;
    loading: boolean;
    error: string | null;
}

export function useSystemInfo() {
    const [state, setState] = useState<SystemInfoState>({
        info: null,
        health: null,
        loading: true,
        error: null
    });

    useEffect(() => {
        let active = true;

        async function load() {
            try {
                const [info, health] = await Promise.all([fetchSystemInfo(), fetchHealthStatus()]);
                if (!active) {
                    return;
                }
                setState({ info, health, loading: false, error: null });
            } catch (error) {
                if (!active) {
                    return;
                }
                const message = error instanceof Error ? error.message : "Backend unavailable";
                setState({ info: null, health: null, loading: false, error: message });
            }
        }

        load();
        return () => {
            active = false;
        };
    }, []);

    return state;
}
