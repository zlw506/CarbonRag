import { DislikeOutlined, LikeOutlined } from "@ant-design/icons";
import { Button, Input, Modal, Space, Tag, message } from "antd";
import { useState } from "react";
import { submitFeedback } from "../services/feedback";
import type { FeedbackRating, FeedbackTargetType } from "../types/feedback";

interface FeedbackButtonGroupProps {
    targetType: FeedbackTargetType;
    traceId: string;
    sessionId?: string | null;
    size?: "small" | "middle" | "large";
}

export function FeedbackButtonGroup({
    targetType,
    traceId,
    sessionId,
    size = "small",
}: FeedbackButtonGroupProps) {
    const [pendingRating, setPendingRating] = useState<FeedbackRating | null>(null);
    const [comment, setComment] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    async function handleSubmit() {
        if (!pendingRating) {
            return;
        }
        setSubmitting(true);
        try {
            await submitFeedback({
                target_type: targetType,
                trace_id: traceId,
                session_id: sessionId ?? undefined,
                rating: pendingRating,
                comment: comment.trim() || undefined,
            });
            setSubmitted(true);
            setPendingRating(null);
            setComment("");
            message.success("反馈已记录。");
        } catch (error) {
            const detail = extractDetailMessage(error);
            message.error(detail ?? "反馈提交失败，请稍后重试。");
        } finally {
            setSubmitting(false);
        }
    }

    return (
        <>
            <Space size={8} wrap>
                <Button
                    size={size}
                    icon={<LikeOutlined />}
                    disabled={submitted}
                    onClick={() => setPendingRating("up")}
                >
                    赞
                </Button>
                <Button
                    size={size}
                    icon={<DislikeOutlined />}
                    disabled={submitted}
                    onClick={() => setPendingRating("down")}
                >
                    踩
                </Button>
                {submitted ? <Tag color="green">已反馈</Tag> : null}
            </Space>
            <Modal
                title="提交反馈"
                open={pendingRating !== null}
                confirmLoading={submitting}
                okText="提交反馈"
                cancelText="取消"
                onCancel={() => {
                    if (submitting) {
                        return;
                    }
                    setPendingRating(null);
                    setComment("");
                }}
                onOk={() => void handleSubmit()}
            >
                <Space direction="vertical" size={12} style={{ width: "100%" }}>
                    <Tag color={pendingRating === "up" ? "green" : "red"}>
                        {pendingRating === "up" ? "正向反馈" : "负向反馈"}
                    </Tag>
                    <Input.TextArea
                        rows={4}
                        maxLength={500}
                        value={comment}
                        onChange={(event) => setComment(event.target.value)}
                        placeholder="可选备注：告诉系统这次回答或计算哪里做得好，或哪里需要改进。"
                    />
                </Space>
            </Modal>
        </>
    );
}

function extractDetailMessage(value: unknown): string | null {
    if (!value || typeof value !== "object") {
        return null;
    }
    const candidate = value as { detail?: unknown };
    return typeof candidate.detail === "string" ? candidate.detail : null;
}
