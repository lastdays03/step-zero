export type OpsUser = {
  id: number;
  email: string;
  full_name: string | null;
  status: string;
  report_count: number;
  last_login_at: string | null;
  is_active: boolean;
  is_superuser: boolean;
  suspended_until: string | null;
  created_at: string;
};

export type DisciplineHistory = {
  id: number;
  user_id: number;
  admin_id: number;
  prev_status: string;
  new_status: string;
  reason: string;
  suspended_until: string | null;
  created_at: string;
};
