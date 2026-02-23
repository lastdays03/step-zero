import { apiClient } from "@/lib/api-client";

import type { OpsUser, DisciplineHistory } from "./types";

export type FetchOpsUsersParams = {
  search?: string;
  status?: string;
};

export async function fetchOpsUsers(params?: FetchOpsUsersParams): Promise<OpsUser[]> {
  const response = await apiClient.get("/ops/users", { params });
  return response.data as OpsUser[];
}

export async function updateUserStatus(
  userId: number,
  data: { status: string; reason: string }
): Promise<OpsUser> {
  const response = await apiClient.patch(`/ops/users/${userId}/status`, data);
  return response.data as OpsUser;
}

export async function bulkUpdateUserStatus(data: {
  user_ids: number[];
  status: string;
  reason: string;
}): Promise<{ updated_count: number }> {
  const response = await apiClient.patch("/ops/users/bulk-status", data);
  return response.data;
}

export async function fetchUserHistory(userId: number): Promise<DisciplineHistory[]> {
  const response = await apiClient.get(`/ops/users/${userId}/history`);
  return response.data as DisciplineHistory[];
}
