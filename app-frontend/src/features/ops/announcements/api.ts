import { apiClient } from "@/lib/api-client";
import { OpsAnnouncement, OpsAnnouncementList, OpsAnnouncementStatus } from "./types";

export const fetchOpsAnnouncements = async (params: {
    skip?: number;
    limit?: number;
    status?: OpsAnnouncementStatus;
}) => {
    const { data } = await apiClient.get<OpsAnnouncementList>("/ops/announcements", { params });
    return data;
};

export const createOpsAnnouncement = async (data: {
    title: string;
    content: string;
    status?: OpsAnnouncementStatus;
}) => {
    const { data: result } = await apiClient.post<OpsAnnouncement>("/ops/announcements", data);
    return result;
};

export const updateOpsAnnouncement = async (
    id: number,
    data: {
        title?: string;
        content?: string;
        status?: OpsAnnouncementStatus;
    }
) => {
    const { data: result } = await apiClient.patch<OpsAnnouncement>(`/ops/announcements/${id}`, data);
    return result;
};

export const deleteOpsAnnouncement = async (id: number) => {
    const { data } = await apiClient.delete<{ status: string }>(`/ops/announcements/${id}`);
    return data;
};
