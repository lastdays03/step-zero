export interface Notification {
    id: number;
    user_id: number;
    content: string;
    type: 'like' | 'comment' | 'reply';
    link?: string;
    is_read: boolean;
    created_at: string;
}
