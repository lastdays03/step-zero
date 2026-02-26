export interface Notification {
    id: number;
    user_id: number;
    content: string;
    type: 'like' | 'comment' | 'reply';
    link?: string;
    is_read: boolean;
    is_deleted: boolean;
    resource_id?: number;
    created_at: string;
}
