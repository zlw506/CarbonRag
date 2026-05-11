import { createContext, useContext, useEffect, useMemo, useState } from "react";
import type { PropsWithChildren } from "react";
import axios from "axios";
import { changePassword, getCurrentUser, loginAccount, logoutAccount, registerAccount, updateProfile } from "../services/auth";
import type { AuthUser, ChangePasswordRequest, LoginRequest, RegisterRequest, UpdateProfileRequest } from "../types/auth";

interface AuthContextValue {
    user: AuthUser | null;
    loading: boolean;
    login: (payload: LoginRequest) => Promise<AuthUser>;
    register: (payload: RegisterRequest) => Promise<AuthUser>;
    logout: () => Promise<void>;
    refresh: () => Promise<AuthUser | null>;
    changePassword: (payload: ChangePasswordRequest) => Promise<AuthUser>;
    updateProfile: (payload: UpdateProfileRequest) => Promise<AuthUser>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: PropsWithChildren) {
    const [user, setUser] = useState<AuthUser | null>(null);
    const [loading, setLoading] = useState(true);

    async function refresh() {
        try {
            const response = await getCurrentUser();
            setUser(response.user);
            return response.user;
        } catch (error) {
            if (axios.isAxiosError(error) && error.response?.status === 401) {
                setUser(null);
                return null;
            }
            throw error;
        } finally {
            setLoading(false);
        }
    }

    useEffect(() => {
        void refresh();
    }, []);

    async function login(payload: LoginRequest) {
        const response = await loginAccount(payload);
        setUser(response.user);
        return response.user;
    }

    async function register(payload: RegisterRequest) {
        const response = await registerAccount(payload);
        return response.user;
    }

    async function logout() {
        try {
            await logoutAccount();
        } finally {
            setUser(null);
        }
    }

    async function handleChangePassword(payload: ChangePasswordRequest) {
        const response = await changePassword(payload);
        setUser(response.user);
        return response.user;
    }

    async function handleUpdateProfile(payload: UpdateProfileRequest) {
        const response = await updateProfile(payload);
        setUser(response.user);
        return response.user;
    }

    const value = useMemo<AuthContextValue>(
        () => ({
            user,
            loading,
            login,
            register,
            logout,
            refresh,
            changePassword: handleChangePassword,
            updateProfile: handleUpdateProfile,
        }),
        [loading, user],
    );

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (!context) {
        throw new Error("useAuth must be used within AuthProvider.");
    }
    return context;
}
