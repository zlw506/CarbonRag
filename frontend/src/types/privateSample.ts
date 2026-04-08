export type PrivateSampleType = "doc" | "table";
export type PrivateSampleBusinessTopic = "energy" | "production" | "logistics" | "project_background";

export interface PrivateSampleCatalogItem {
    doc_id: string;
    title: string;
    source_type: "private_sample";
    sample_type: PrivateSampleType;
    business_topic: PrivateSampleBusinessTopic;
    session_attachable: boolean;
}
