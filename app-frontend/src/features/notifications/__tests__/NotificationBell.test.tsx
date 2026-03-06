import React from 'react';
import { act, fireEvent, render, screen } from '@testing-library/react';
import { NotificationBell } from '../components/NotificationBell';

// ---- Mocks ----

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 1, email: 'test@test.com' } }),
}));

jest.mock('@/features/growth-club/hooks/useTimeAgo', () => ({
  formatTimeAgo: (d: string) => d,
}));

jest.mock('../api', () => ({
  notificationsApi: {
    getNotifications: jest.fn(),
    readAllNotifications: jest.fn(),
    markAsRead: jest.fn(),
    deleteNotification: jest.fn(),
  },
}));

import { notificationsApi } from '../api';

const mockGetNotifications = notificationsApi.getNotifications as jest.Mock;
const mockReadAll = notificationsApi.readAllNotifications as jest.Mock;
const mockMarkAsRead = notificationsApi.markAsRead as jest.Mock;

const sampleNotifications = [
  { id: 1, content: '새 댓글', type: 'comment', is_read: false, created_at: '2026-01-01T00:00:00Z', link: '/posts/1' },
  { id: 2, content: '좋아요', type: 'like', is_read: true, created_at: '2026-01-02T00:00:00Z' },
];

beforeEach(() => {
  jest.clearAllMocks();
  jest.useFakeTimers();
  mockGetNotifications.mockResolvedValue(sampleNotifications);
  mockReadAll.mockResolvedValue(undefined);
  mockMarkAsRead.mockResolvedValue(undefined);
});

afterEach(() => {
  jest.runOnlyPendingTimers();
  jest.useRealTimers();
});

async function flushMicrotasks(count: number = 3) {
  for (let index = 0; index < count; index += 1) {
    await Promise.resolve();
  }
}

async function renderNotificationBell() {
  render(<NotificationBell />);

  await act(async () => {
    jest.runOnlyPendingTimers();
    await flushMicrotasks();
  });
  expect(mockGetNotifications).toHaveBeenCalled();
}

describe('NotificationBell', () => {
  it('렌더링 시 벨 아이콘 표시', async () => {
    await renderNotificationBell();

    // 벨 버튼이 있어야 함
    const button = screen.getByRole('button');
    expect(button).toBeDefined();
  });

  it('미읽은 알림이 있으면 인디케이터 표시', async () => {
    await renderNotificationBell();

    // unread indicator (animate-pulse class)
    const indicator = document.querySelector('.animate-pulse');
    expect(indicator).not.toBeNull();
  });

  it('클릭 시 드롭다운 열림 + 알림 목록 표시', async () => {
    await renderNotificationBell();

    fireEvent.click(screen.getByRole('button'));

    expect(screen.getByText('새 댓글')).toBeDefined();
    expect(screen.getByText('좋아요')).toBeDefined();
  });

  it('모두 읽음 버튼 클릭 시 readAllNotifications 호출', async () => {
    await renderNotificationBell();

    fireEvent.click(screen.getByRole('button'));

    const readAllBtn = screen.getByText('모두 읽음');
    await act(async () => {
      fireEvent.click(readAllBtn);
      await flushMicrotasks();
    });

    expect(mockReadAll).toHaveBeenCalled();
  });

  it('알림 목록이 비어있으면 빈 상태 메시지 표시', async () => {
    mockGetNotifications.mockResolvedValue([]);

    await renderNotificationBell();

    fireEvent.click(screen.getByRole('button'));

    expect(screen.getByText('새로운 알림이 없습니다.')).toBeDefined();
  });
});
