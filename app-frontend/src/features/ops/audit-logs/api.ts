import { apiClient } from "@/lib/api-client";
import { AuditLog } from "./types";

export const fetchAuditLogs = async (): Promise<AuditLog[]> => {
    const response = await apiClient.get<AuditLog[]>("/ops/audit-logs");
    return response.data;
};
