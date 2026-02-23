import { apiClient } from "@/lib/api-client";

import type { OpsAuditLogList, OpsAuditLogQuery } from "./types";

export async function fetchOpsAuditLogs(query: OpsAuditLogQuery = {}): Promise<OpsAuditLogList> {
  const params: Record<string, string | number> = {};

  if (typeof query.actor === "number") params.actor = query.actor;
  if (query.action) params.action = query.action;
  if (query.targetType) params.target_type = query.targetType;
  if (query.from) params.from = query.from;
  if (query.to) params.to = query.to;
  if (typeof query.page === "number") params.page = query.page;
  if (typeof query.size === "number") params.size = query.size;

  const response = await apiClient.get<OpsAuditLogList>("/ops/audit-logs", { params });
  return response.data;
}
