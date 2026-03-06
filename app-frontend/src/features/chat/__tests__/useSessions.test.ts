import { act, renderHook, waitFor } from '@testing-library/react';

import { useSessions } from '../hooks/useSessions';

const mockSetCurrentSessionId = jest.fn();

const providerState = {
  currentSessionId: null as string | null,
  setCurrentSessionId: mockSetCurrentSessionId,
  refreshSessionList: jest.fn(),
  sessionListVersion: 0,
  publishSessionPreview: jest.fn(),
  sessionPreview: null as {
    id: string;
    title?: string | null;
    message_count?: number;
    roadmap_id?: string | null;
    step_id?: number | null;
    created_at?: string;
    updated_at: string;
  } | null,
  sessionPreviewVersion: 0,
  roadmapContext: null,
};

jest.mock('../providers/ChatProvider', () => ({
  useChatProvider: () => providerState,
}));

jest.mock('../utils/api', () => ({
  fetchSessions: jest.fn(),
  createSession: jest.fn(),
  updateSessionTitle: jest.fn(),
  deleteSession: jest.fn(),
}));

import { fetchSessions } from '../utils/api';

const mockFetchSessions = fetchSessions as jest.Mock;

beforeEach(() => {
  jest.clearAllMocks();
  providerState.currentSessionId = null;
  providerState.sessionListVersion = 0;
  providerState.sessionPreview = null;
  providerState.sessionPreviewVersion = 0;
});

describe('useSessions', () => {
  it('session id만 바뀌면 조기 재조회를 보내지 않는다', () => {
    const { rerender } = renderHook(() => useSessions());

    act(() => {
      providerState.currentSessionId = 'sess-new';
      rerender();
    });

    expect(mockFetchSessions).not.toHaveBeenCalled();
  });

  it('새 세션 preview를 즉시 목록 맨 위에 반영한다', async () => {
    const { result, rerender } = renderHook(() => useSessions());

    act(() => {
      providerState.sessionPreview = {
        id: 'sess-new',
        title: '첫 질문',
        message_count: 1,
        created_at: '2026-03-06T00:00:00.000Z',
        updated_at: '2026-03-06T00:00:00.000Z',
      };
      providerState.sessionPreviewVersion = 1;
      rerender();
    });

    await waitFor(() => {
      expect(result.current.sessions[0]?.id).toBe('sess-new');
    });

    expect(result.current.sessions[0]).toMatchObject({
      title: '첫 질문',
      message_count: 1,
    });
  });

  it('preview 중간에 도착해도 늦게 끝난 목록 응답이 새 세션을 지우지 않는다', async () => {
    let resolveFetch:
      | ((value: { sessions: []; total: number }) => void)
      | undefined;

    mockFetchSessions.mockReturnValueOnce(
      new Promise((resolve) => {
        resolveFetch = resolve;
      }),
    );

    const { result, rerender } = renderHook(() => useSessions());

    act(() => {
      void result.current.loadSessions();
    });

    act(() => {
      providerState.sessionPreview = {
        id: 'sess-new',
        title: '첫 질문',
        message_count: 1,
        created_at: '2026-03-06T00:00:00.000Z',
        updated_at: '2026-03-06T00:00:00.000Z',
      };
      providerState.sessionPreviewVersion = 1;
      rerender();
    });

    await waitFor(() => {
      expect(result.current.sessions[0]?.id).toBe('sess-new');
    });

    await act(async () => {
      resolveFetch?.({ sessions: [], total: 0 });
    });

    await waitFor(() => {
      expect(result.current.sessions[0]?.id).toBe('sess-new');
    });

    mockFetchSessions.mockResolvedValueOnce({
      sessions: [
        {
          id: 'sess-new',
          title: '첫 질문',
          message_count: 2,
          roadmap_id: null,
          step_id: null,
          created_at: '2026-03-06T00:00:00.000Z',
          updated_at: '2026-03-06T00:00:05.000Z',
        },
      ],
      total: 1,
    });

    await act(async () => {
      await result.current.loadSessions();
    });

    expect(result.current.sessions[0]).toMatchObject({
      id: 'sess-new',
      message_count: 2,
      updated_at: '2026-03-06T00:00:05.000Z',
    });
  });
});
