import env from "../app/env";
import type { FilePreviewResponse, FilePreviewTarget } from "../types/filePreview";
import { httpClient } from "./http";

function buildPath(target: FilePreviewTarget, raw = false) {
    const path = `/v1/file-previews/${encodeURIComponent(target.sourceType)}/${encodeURIComponent(target.sourceId)}${raw ? "/raw" : ""}`;
    const params = new URLSearchParams();
    if (target.kbId) {
        params.set("kb_id", target.kbId);
    }
    const query = params.toString();
    return query ? `${path}?${query}` : path;
}

export async function getFilePreview(target: FilePreviewTarget) {
    const response = await httpClient.get<FilePreviewResponse>(buildPath(target));
    return response.data;
}

export function buildFilePreviewRawUrl(target: FilePreviewTarget) {
    const base = env.apiBaseUrl.replace(/\/+$/, "");
    return `${base}${buildPath(target, true)}`;
}
