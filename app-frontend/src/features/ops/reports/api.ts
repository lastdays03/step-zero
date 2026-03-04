import { apiClient } from "@/lib/api-client";

import type { OpsSummary } from "./types";

export async function fetchOpsSummary(
  range: "7d" | "30d" = "7d",
): Promise<OpsSummary> {
  const response = await apiClient.get("/ops/reports/summary", {
    params: { range },
  });
  return response.data as OpsSummary;
}
