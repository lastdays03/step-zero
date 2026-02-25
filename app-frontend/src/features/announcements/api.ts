import { apiClient } from '@/lib/api-client';

export interface Announcement {
    id: number;
    title: string;
    content: string;
    published_at: string;
}

export const announcementsApi = {
    getAnnouncement: async (id: number): Promise<Announcement> => {
        const response = await apiClient.get(`/announcements/${id}`);
        return response.data;
    },
    getAnnouncements: async (): Promise<Announcement[]> => {
        const response = await apiClient.get('/announcements');
        return response.data;
    }
};
