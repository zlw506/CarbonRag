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
            message.success(`欢迎回来，${loggedInUser.username}。`);
            navigate(loggedInUser.password_must_change ? "/change-password" : redirectTarget, { replace: true });
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "登录失败，请检查用户名和密码。");
        } finally {
            setSubmitting(false);
        }
    }

    async function handleRegister(values: FormValues) {
        setSubmitting(true);
        setErrorMessage(null);
        try {
            const createdUser = await register(values);
            if (createdUser.username === "admin" && createdUser.role === "admin") {
                message.success("初始管理员已恢复，请使用 admin / 123456 登录，并在首次进入后立即修改密码。");
            } else {
                message.success(`账号 ${createdUser.username} 已创建，请登录。`);
            }
            setActiveTab("login");
            loginForm.setFieldsValue({ username: createdUser.username, password: values.password });
            registerForm.resetFields();
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "注册失败，请稍后重试。");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="auth-shell">
            <Card className="auth-card">
                <Typography.Title level={2}>CarbonRag 登录</Typography.Title>
                <Typography.Paragraph type="secondary">
                    V1.0.0 已引入本地账号、用户数据隔离和管理员入口。登录后才能访问你自己的会话、报告、核算结果和反馈记录。
                </Typography.Paragraph>
                <Typography.Paragraph type="secondary">
                    如需恢复初始管理员，可在注册页输入 `admin` / `123456`。系统会恢复保底管理员账号，并要求首次登录后立即修改密码。
                </Typography.Paragraph>
                {errorMessage ? (
                    <Alert
                        showIcon
                        type="warning"
                        message="身份认证提示"
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
                            label: "登录",
                            children: (
                                <Form<FormValues> form={loginForm} layout="vertical" onFinish={handleLogin}>
                                    <Form.Item
                                        label="用户名"
                                        name="username"
                                        rules={[{ required: true, message: "请输入用户名。" }]}
                                    >
                                        <Input prefix={<UserOutlined />} autoComplete="username" />
                                    </Form.Item>
                                    <Form.Item
                                        label="密码"
                                        name="password"
                                        rules={[{ required: true, message: "请输入密码。" }]}
                                    >
                                        <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
                                    </Form.Item>
                                    <Button type="primary" htmlType="submit" block loading={submitting}>
                                        登录
                                    </Button>
                                </Form>
                            ),
                        },
                        {
                            key: "register",
                            label: "注册",
                            children: (
                                <Form<FormValues> form={registerForm} layout="vertical" onFinish={handleRegister}>
                                    <Form.Item
                                        label="用户名"
                                        name="username"
                                        rules={[{ required: true, message: "请输入用户名。" }]}
                                        extra="仅允许小写字母、数字、下划线和连字符。"
                                    >
                                        <Input prefix={<UserOutlined />} autoComplete="username" />
                                    </Form.Item>
                                    <Form.Item
                                        label="密码"
                                        name="password"
                                        rules={[{ required: true, message: "请输入密码。" }]}
                                        extra="至少 6 位字符。"
                                    >
                                        <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                                    </Form.Item>
                                    <Button htmlType="submit" block loading={submitting}>
                                        创建账号
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
