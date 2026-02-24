export interface AuditLog {
    id: number;
    user_id: number;
    actor_name: string;
    action: string;
    target_type: string;
    target_id: string;
    target_author: string | null;
    details: string | null;
    created_at: string;
}
