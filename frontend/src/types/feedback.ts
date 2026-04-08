export type FeedbackTargetType = "ask" | "calc_carbon";
export type FeedbackRating = "up" | "down";

export interface FeedbackRequest {
    target_type: FeedbackTargetType;
    trace_id: string;
    session_id?: string;
    rating: FeedbackRating;
    comment?: string;
}

export interface FeedbackResponse {
    status: "ok";
    feedback_id: string;
    created_at: string;
}
