import { renderHook, waitFor, act } from '@testing-library/react';
import { useNotifications } from '../hooks/useNotifications';

jest.mock('../api', () => ({
  notificationsApi: {
    getNotifications: jest.fn(),
    markAsRead: jest.fn(),
    readAllNotifications: jest.fn(),
  },
}));

jest.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ isLoggedIn: true }),
}));

import { notificationsApi } from '../api';

const mockGetNotifications = notificationsApi.getNotifications as jest.Mock;
const mockMarkAsRead = notificationsApi.markAsRead as jest.Mock;
const mockReadAllNotifications = notificationsApi.readAllNotifications as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
});

afterEach(() => jest.useRealTimers());

describe('useNotifications', () => {
  it('마운트 시 알림 목록 fetch', async () => {
    const data = [
      { id: 1, message: '새 댓글', is_read: false },
      { id: 2, message: '좋아요', is_read: true },
    ];
    mockGetNotifications.mockResolvedValue(data);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => {
      expect(result.current.notifications).toHaveLength(2);
    });

    expect(result.current.unreadCount).toBe(1);
  });

  it('markRead: 개별 알림 읽음 처리 (낙관적 업데이트)', async () => {
    mockGetNotifications.mockResolvedValue([{ id: 1, message: 'test', is_read: false }]);
    mockMarkAsRead.mockResolvedValue({});

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.notifications).toHaveLength(1));

    await act(async () => {
      await result.current.markRead(1);
    });

    expect(result.current.notifications[0].is_read).toBe(true);
    expect(result.current.unreadCount).toBe(0);
  });

  it('markAllRead: 전체 알림 읽음 처리', async () => {
    mockGetNotifications.mockResolvedValue([
      { id: 1, is_read: false },
      { id: 2, is_read: false },
    ]);
    mockReadAllNotifications.mockResolvedValue(undefined);

    const { result } = renderHook(() => useNotifications());

    await waitFor(() => expect(result.current.unreadCount).toBe(2));

    await act(async () => {
      await result.current.markAllRead();
    });

    expect(result.current.unreadCount).toBe(0);
  });
});
