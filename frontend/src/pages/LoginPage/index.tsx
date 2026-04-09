import { LockOutlined, UserOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Form, Input, Tabs, Typography, message } from "antd";
import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";

type AuthTab = "login" | "register";

interface FormValues {
    username: string;
    password: string;
}

export function LoginPage() {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, loading, login, register } = useAuth();
    const [activeTab, setActiveTab] = useState<AuthTab>("login");
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [loginForm] = Form.useForm<FormValues>();
    const [registerForm] = Form.useForm<FormValues>();

    const redirectTarget = useMemo(() => {
        const state = location.state as { from?: { pathname?: string } } | null;
        return state?.from?.pathname && state.from.pathname !== "/login" ? state.from.pathname : "/";
    }, [location.state]);

    useEffect(() => {
        if (loading || !user) {
            return;
        }
        navigate(user.password_must_change ? "/change-password" : redirectTarget, { replace: true });
    }, [loading, navigate, redirectTarget, user]);

    async function handleLogin(values: FormValues) {
        setSubmitting(true);
        setErrorMessage(null);
        try {
            const loggedInUser = await login(values);
            message.success(`Welcome back, ${loggedInUser.username}.`);
            navigate(loggedInUser.password_must_change ? "/change-password" : redirectTarget, { replace: true });
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Login failed. Please check your username and password.");
        } finally {
            setSubmitting(false);
        }
    }

    async function handleRegister(values: FormValues) {
        setSubmitting(true);
        setErrorMessage(null);
        try {
            const createdUser = await register(values);
            message.success(`User ${createdUser.username} created. Please sign in.`);
            setActiveTab("login");
            loginForm.setFieldsValue({ username: createdUser.username, password: values.password });
            registerForm.resetFields();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Registration failed.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="auth-shell">
            <Card className="auth-card">
                <Typography.Title level={2}>CarbonRag Sign In</Typography.Title>
                <Typography.Paragraph type="secondary">
                    V1.0.0 introduces local accounts, user isolation, and an admin entry. Sign in to access your own
                    sessions, reports, calculations, and feedback.
                </Typography.Paragraph>
                {errorMessage ? (
                    <Alert
                        showIcon
                        type="warning"
                        message="Authentication Error"
                        description={errorMessage}
                        className="auth-card__alert"
                    />
                ) : null}
                <Tabs
                    activeKey={activeTab}
                    onChange={(key) => {
                        setActiveTab(key as AuthTab);
                        setErrorMessage(null);
                    }}
                    items={[
                        {
                            key: "login",
                            label: "Login",
                            children: (
                                <Form<FormValues> form={loginForm} layout="vertical" onFinish={handleLogin}>
                                    <Form.Item
                                        label="Username"
                                        name="username"
                                        rules={[{ required: true, message: "Username is required." }]}
                                    >
                                        <Input prefix={<UserOutlined />} autoComplete="username" />
                                    </Form.Item>
                                    <Form.Item
                                        label="Password"
                                        name="password"
                                        rules={[{ required: true, message: "Password is required." }]}
                                    >
                                        <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
                                    </Form.Item>
                                    <Button type="primary" htmlType="submit" block loading={submitting}>
                                        Sign In
                                    </Button>
                                </Form>
                            ),
                        },
                        {
                            key: "register",
                            label: "Register",
                            children: (
                                <Form<FormValues> form={registerForm} layout="vertical" onFinish={handleRegister}>
                                    <Form.Item
                                        label="Username"
                                        name="username"
                                        rules={[{ required: true, message: "Username is required." }]}
                                        extra="Lowercase letters, digits, '_' and '-' only."
                                    >
                                        <Input prefix={<UserOutlined />} autoComplete="username" />
                                    </Form.Item>
                                    <Form.Item
                                        label="Password"
                                        name="password"
                                        rules={[{ required: true, message: "Password is required." }]}
                                        extra="At least 6 characters."
                                    >
                                        <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                                    </Form.Item>
                                    <Button htmlType="submit" block loading={submitting}>
                                        Create Account
                                    </Button>
                                </Form>
                            ),
                        },
                    ]}
                />
            </Card>
        </div>
    );
}

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
