import { notificationsApi } from '../api';

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;
const mockDelete = apiClient.delete as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('notificationsApi', () => {
  describe('getNotifications', () => {
    it('알림 목록 조회', async () => {
      const notifications = [{ id: 1, message: '새 댓글', is_read: false }];
      mockGet.mockResolvedValue({ data: notifications });
      const result = await notificationsApi.getNotifications();
      expect(mockGet).toHaveBeenCalledWith('/notifications');
      expect(result).toEqual(notifications);
    });
  });

  describe('markAsRead', () => {
    it('개별 알림 읽음 처리', async () => {
      mockPost.mockResolvedValue({ data: { status: 'success' } });
      await notificationsApi.markAsRead(1);
      expect(mockPost).toHaveBeenCalledWith('/notifications/1/read');
    });
  });

  describe('readAllNotifications', () => {
    it('전체 알림 읽음 처리', async () => {
      mockPost.mockResolvedValue({});
      await notificationsApi.readAllNotifications();
      expect(mockPost).toHaveBeenCalledWith('/notifications/read-all');
    });
  });

  describe('deleteNotification', () => {
    it('개별 알림 삭제', async () => {
      mockDelete.mockResolvedValue({});
      await notificationsApi.deleteNotification(1);
      expect(mockDelete).toHaveBeenCalledWith('/notifications/1');
    });
  });
});
