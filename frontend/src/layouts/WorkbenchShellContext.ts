import { useOutletContext } from "react-router-dom";
import type { SessionSummary } from "../types/session";

export interface WorkbenchShellContextValue {
    sessions: SessionSummary[];
    activeSessionId: string | null;
    loadingSessions: boolean;
    sessionRailCollapsed: boolean;
    createSession: () => Promise<void>;
    refreshSessions: (preferredSessionId?: string | null) => Promise<SessionSummary[]>;
    selectSession: (sessionId: string) => void;
    toggleSessionRail: () => void;
}

export function useWorkbenchShellContext() {
    return useOutletContext<WorkbenchShellContextValue>();
}
