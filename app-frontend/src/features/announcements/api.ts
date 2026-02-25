import { apiClient } from "@/lib/api-client";
import type { OpsAnnouncement } from "../ops/announcements/types";

/** GET /announcements -- 공지 목록 조회 */
export async function fetchPublishedAnnouncements(): Promise<OpsAnnouncement[]> {
    const { data } = await apiClient.get<OpsAnnouncement[]>("/announcements");
    return data;
}

/** GET /announcements/:id -- 공지 상세 조회 */
export async function fetchPublishedAnnouncement(id: number): Promise<OpsAnnouncement> {
    const { data } = await apiClient.get<OpsAnnouncement>(`/announcements/${id}`);
    return data;
}

export const announcementsApi = {
    fetchPublishedAnnouncements,
    fetchPublishedAnnouncement,
};
