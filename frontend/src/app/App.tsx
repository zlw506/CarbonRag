import { App as AntdApp } from "antd";
import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import { router } from "../router";

export function App() {
    return (
        <AntdApp>
            <AuthProvider>
                <RouterProvider router={router} />
            </AuthProvider>
        </AntdApp>
    );
}
