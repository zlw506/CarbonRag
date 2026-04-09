import { LockOutlined } from "@ant-design/icons";
import { Alert, Button, Card, Form, Input, Typography, message } from "antd";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../../app/AuthContext";

interface ChangePasswordFormValues {
    current_password: string;
    new_password: string;
    confirm_password: string;
}

export function ChangePasswordPage() {
    const navigate = useNavigate();
    const { user, loading, changePassword } = useAuth();
    const [submitting, setSubmitting] = useState(false);
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [form] = Form.useForm<ChangePasswordFormValues>();

    useEffect(() => {
        if (loading) {
            return;
        }
        if (!user) {
            navigate("/login", { replace: true });
            return;
        }
        if (!user.password_must_change) {
            navigate("/", { replace: true });
        }
    }, [loading, navigate, user]);

    async function handleSubmit(values: ChangePasswordFormValues) {
        setSubmitting(true);
        setErrorMessage(null);
        try {
            await changePassword({
                current_password: values.current_password,
                new_password: values.new_password,
            });
            message.success("Password updated.");
            navigate("/", { replace: true });
        } catch (error) {
            setErrorMessage(extractDetailMessage(error) ?? "Password change failed.");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <div className="auth-shell">
            <Card className="auth-card">
                <Typography.Title level={2}>Change Password</Typography.Title>
                <Typography.Paragraph type="secondary">
                    The initial admin account and any reset password flow must complete this step before entering the
                    workbench.
                </Typography.Paragraph>
                {errorMessage ? (
                    <Alert
                        showIcon
                        type="warning"
                        message="Password Update Error"
                        description={errorMessage}
                        className="auth-card__alert"
                    />
                ) : null}
                <Form<ChangePasswordFormValues> form={form} layout="vertical" onFinish={handleSubmit}>
                    <Form.Item
                        label="Current Password"
                        name="current_password"
                        rules={[{ required: true, message: "Current password is required." }]}
                    >
                        <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
                    </Form.Item>
                    <Form.Item
                        label="New Password"
                        name="new_password"
                        rules={[{ required: true, message: "New password is required." }]}
                    >
                        <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                    </Form.Item>
                    <Form.Item
                        label="Confirm New Password"
                        name="confirm_password"
                        dependencies={["new_password"]}
                        rules={[
                            { required: true, message: "Please confirm the new password." },
                            ({ getFieldValue }) => ({
                                validator(_, value) {
                                    if (!value || value === getFieldValue("new_password")) {
                                        return Promise.resolve();
                                    }
                                    return Promise.reject(new Error("Passwords do not match."));
                                },
                            }),
                        ]}
                    >
                        <Input.Password prefix={<LockOutlined />} autoComplete="new-password" />
                    </Form.Item>
                    <Button type="primary" htmlType="submit" block loading={submitting}>
                        Update Password
                    </Button>
                </Form>
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
