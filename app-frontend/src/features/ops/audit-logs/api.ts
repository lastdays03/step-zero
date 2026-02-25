import { apiClient } from "@/lib/api-client";
import { AuditLog } from "./types";

export interface AuditLogFilters {
    action?: string;
    target_type?: string;
    keyword?: string;
    date_from?: string;
    date_to?: string;
    limit?: number;
    offset?: number;
}

export const fetchAuditLogs = async (filters: AuditLogFilters = {}): Promise<AuditLog[]> => {
    const params = new URLSearchParams();
    if (filters.action) params.set("action", filters.action);
    if (filters.target_type) params.set("target_type", filters.target_type);
    if (filters.keyword) params.set("keyword", filters.keyword);
    if (filters.date_from) params.set("date_from", filters.date_from);
    if (filters.date_to) params.set("date_to", filters.date_to);
    if (filters.limit != null) params.set("limit", String(filters.limit));
    if (filters.offset != null) params.set("offset", String(filters.offset));

    const query = params.toString() ? `?${params.toString()}` : "";
    const response = await apiClient.get<AuditLog[]>(`/ops/audit-logs${query}`);
    return response.data;
};
