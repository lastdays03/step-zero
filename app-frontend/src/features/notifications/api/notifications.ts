import { apiClient } from '@/lib/api-client';

export interface Notification {
    id: number;
    user_id: number;
    actor_id: number | null;
    action_type: string;
    target_id: number | null;
    target_type: string | null;
    message: string;
    is_read: boolean;
    created_at: string;
}

export const notificationsApi = {
    getNotifications: async (): Promise<Notification[]> => {
        const res = await apiClient.get<Notification[]>('/notifications');
        return res.data;
    },

    markRead: async (notificationId: number): Promise<Notification> => {
        const res = await apiClient.put<Notification>(`/notifications/${notificationId}/read`);
        return res.data;
    },

    markAllRead: async (): Promise<void> => {
        await apiClient.put('/notifications/read-all');
    },
};
