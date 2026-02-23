import { apiClient } from "@/lib/api-client";

import type { OpsUser } from "./types";

export async function fetchOpsUsers(): Promise<OpsUser[]> {
  const response = await apiClient.get("/ops/users");
  return response.data as OpsUser[];
}
