import { Spin } from "antd";
import { createBrowserRouter, Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../app/AuthContext";
import { AppShell } from "../layouts/AppShell";
import { AdminPlaceholderPage } from "../pages/AdminPlaceholderPage";
import { AskPage } from "../pages/AskPage";
import { CarbonCalcPage } from "../pages/CarbonCalcPage";
import { ChangePasswordPage } from "../pages/ChangePasswordPage";
import { LoginPage } from "../pages/LoginPage";
import { ReportPage } from "../pages/ReportPage";

function FullscreenLoading() {
    return (
        <div className="auth-shell">
            <div className="auth-loading">
                <Spin size="large" />
            </div>
        </div>
    );
}

function GuestOnlyRoute() {
    const { user, loading } = useAuth();

    if (loading) {
        return <FullscreenLoading />;
    }
    if (!user) {
        return <Outlet />;
    }
    return <Navigate to={user.password_must_change ? "/change-password" : "/"} replace />;
}

function PasswordChangeRoute() {
    const { user, loading } = useAuth();

    if (loading) {
        return <FullscreenLoading />;
    }
    if (!user) {
        return <Navigate to="/login" replace />;
    }
    if (!user.password_must_change) {
        return <Navigate to="/" replace />;
    }
    return <Outlet />;
}

function ProtectedRoute() {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return <FullscreenLoading />;
    }
    if (!user) {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }
    if (user.password_must_change) {
        return <Navigate to="/change-password" replace />;
    }
    return <Outlet />;
}

function AdminRoute() {
    const { user, loading } = useAuth();
    const location = useLocation();

    if (loading) {
        return <FullscreenLoading />;
    }
    if (!user) {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }
    if (user.password_must_change) {
        return <Navigate to="/change-password" replace />;
    }
    if (user.role !== "admin") {
        return <Navigate to="/" replace />;
    }
    return <Outlet />;
}

export const router = createBrowserRouter([
    {
        element: <GuestOnlyRoute />,
        children: [
            { path: "/login", element: <LoginPage /> },
        ],
    },
    {
        element: <PasswordChangeRoute />,
        children: [
            { path: "/change-password", element: <ChangePasswordPage /> },
        ],
    },
    {
        element: <ProtectedRoute />,
        children: [
            {
                path: "/",
                element: <AppShell />,
                children: [
                    { index: true, element: <AskPage /> },
                    { path: "carbon-calc", element: <CarbonCalcPage /> },
                    { path: "report", element: <ReportPage /> },
                    {
                        element: <AdminRoute />,
                        children: [{ path: "admin", element: <AdminPlaceholderPage /> }],
                    },
                ],
            },
        ],
    },
    { path: "*", element: <Navigate to="/" replace /> },
]);
