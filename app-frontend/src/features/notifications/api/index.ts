import { apiClient } from '@/lib/api-client';
import type { Notification } from '../types';

export type { Notification } from '../types';

export const notificationsApi = {
    getNotifications: async (): Promise<Notification[]> => {
        const response = await apiClient.get<Notification[]>('/notifications');
        return response.data;
    },

    readAllNotifications: async (): Promise<void> => {
        await apiClient.post('/notifications/read-all');
    },

    markAsRead: async (id: number): Promise<void> => {
        await apiClient.post(`/notifications/${id}/read`);
    },

    deleteNotification: async (id: number): Promise<void> => {
        await apiClient.delete(`/notifications/${id}`);
    }
};
