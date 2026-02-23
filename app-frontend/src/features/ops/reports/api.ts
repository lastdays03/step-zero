import { apiClient } from "@/lib/api-client";

import type { OpsSummary } from "./types";

export async function fetchOpsSummary(): Promise<OpsSummary> {
  const response = await apiClient.get("/ops/reports/summary");
  return response.data as OpsSummary;
}
