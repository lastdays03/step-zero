import { notificationsApi } from '../api/notifications';

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';

const mockGet = apiClient.get as jest.Mock;
const mockPut = apiClient.put as jest.Mock;

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

  describe('markRead', () => {
    it('개별 알림 읽음 처리', async () => {
      const updated = { id: 1, is_read: true };
      mockPut.mockResolvedValue({ data: updated });
      const result = await notificationsApi.markRead(1);
      expect(mockPut).toHaveBeenCalledWith('/notifications/1/read');
      expect(result).toEqual(updated);
    });
  });

  describe('markAllRead', () => {
    it('전체 알림 읽음 처리', async () => {
      mockPut.mockResolvedValue({});
      await notificationsApi.markAllRead();
      expect(mockPut).toHaveBeenCalledWith('/notifications/read-all');
    });
  });
});
