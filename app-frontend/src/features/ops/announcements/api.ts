import { apiClient } from "@/lib/api-client";

import type {
  OpsAnnouncement,
  OpsAnnouncementList,
  OpsAnnouncementStatus,
} from "./types";

/** GET /ops/announcements -- 공지 목록 조회 */
export async function fetchOpsAnnouncements(): Promise<OpsAnnouncementList> {
  const { data } = await apiClient.get<OpsAnnouncementList>(
    "/ops/announcements",
  );
  return data;
}

/** POST /ops/announcements -- 공지 생성 (초안) */
export async function createOpsAnnouncement(payload: {
  title: string;
  content: string;
}): Promise<OpsAnnouncement> {
  const { data } = await apiClient.post<OpsAnnouncement>(
    "/ops/announcements",
    payload,
  );
  return data;
}

/** PATCH /ops/announcements/:id -- 공지 제목/내용 수정 */
export async function updateOpsAnnouncement(
  id: number,
  payload: { title?: string; content?: string },
): Promise<OpsAnnouncement> {
  const { data } = await apiClient.patch<OpsAnnouncement>(
    `/ops/announcements/${id}`,
    payload,
  );
  return data;
}

/** PATCH /ops/announcements/:id/status -- 공지 상태 변경 */
export async function updateOpsAnnouncementStatus(
  id: number,
  status: OpsAnnouncementStatus,
): Promise<OpsAnnouncement> {
  const { data } = await apiClient.patch<OpsAnnouncement>(
    `/ops/announcements/${id}/status`,
    { status },
    { headers: { "Content-Type": "application/json" } },
  );
  return data;
}
