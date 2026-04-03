import { createBrowserRouter } from "react-router-dom";
import { AppShell } from "../layouts/AppShell";
import { AskPage } from "../pages/AskPage";
import { CarbonCalcPage } from "../pages/CarbonCalcPage";
import { ReportPage } from "../pages/ReportPage";
import { AdminPlaceholderPage } from "../pages/AdminPlaceholderPage";

export const router = createBrowserRouter([
    {
        path: "/",
        element: <AppShell />,
        children: [
            { index: true, element: <AskPage /> },
            { path: "carbon-calc", element: <CarbonCalcPage /> },
            { path: "report", element: <ReportPage /> },
            { path: "admin", element: <AdminPlaceholderPage /> }
        ]
    }
]);
