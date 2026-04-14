import { RouterProvider } from "react-router-dom";
import { AuthProvider } from "./AuthContext";
import { SettingsProvider } from "./SettingsContext";
import { ThemeProvider } from "./ThemeContext";
import { router } from "../router";

export function App() {
    return (
        <ThemeProvider>
            <AuthProvider>
                <SettingsProvider>
                    <RouterProvider router={router} />
                </SettingsProvider>
            </AuthProvider>
        </ThemeProvider>
    );
}
