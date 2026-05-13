import { useOutletContext } from "react-router-dom";
import type { SessionSummary } from "../types/session";

export interface WorkbenchShellContextValue {
    sessions: SessionSummary[];
    activeSessionId: string | null;
    loadingSessions: boolean;
    sessionRailCollapsed: boolean;
    createSession: () => Promise<SessionSummary | null>;
    refreshSessions: (preferredSessionId?: string | null) => Promise<SessionSummary[]>;
    syncSessionSummary: (session: SessionSummary, options?: { activate?: boolean }) => void;
    updateSessionSummary: (sessionId: string, patch: Partial<SessionSummary>) => void;
    selectSession: (sessionId: string) => void;
    toggleSessionRail: () => void;
    startNewDraftSession: () => void;
}

export function useWorkbenchShellContext() {
    return useOutletContext<WorkbenchShellContextValue>();
}
