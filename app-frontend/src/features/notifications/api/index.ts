import { apiClient } from '@/lib/api-client';
import { Notification } from '../types';

export const notificationsApi = {
    getNotifications: async (): Promise<Notification[]> => {
        const response = await apiClient.get('/notifications');
        return response.data;
    },

    readAllNotifications: async (): Promise<void> => {
        await apiClient.post('/notifications/read-all');
    },

    markAsRead: async (id: number): Promise<void> => {
        await apiClient.post(`/notifications/${id}/read`);
    }
};
