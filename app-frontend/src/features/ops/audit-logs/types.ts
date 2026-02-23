export type OpsAuditLogItem = {
  id: number;
  admin_id: number;
  action: string;
  target_type: string;
  target_id: string | null;
  reason: string | null;
  meta: Record<string, unknown>;
  created_at: string;
};

export type OpsAuditLogList = {
  items: OpsAuditLogItem[];
  total: number;
  page: number;
  size: number;
};

export type OpsAuditLogQuery = {
  actor?: number;
  action?: string;
  targetType?: string;
  from?: string;
  to?: string;
  page?: number;
  size?: number;
};
