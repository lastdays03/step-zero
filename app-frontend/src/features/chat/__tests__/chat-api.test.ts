import { fetchSessions, createSession, fetchMessages, updateSessionTitle, deleteSession } from '../utils/api';

const mockFetch = jest.fn();
global.fetch = mockFetch;

jest.mock('../utils/sse', () => ({
  getApiBaseUrl: () => 'http://localhost:8000/api/v1',
  getAuthHeaders: () => ({ 'Content-Type': 'application/json', Authorization: 'Bearer test-token' }),
  tryRefreshToken: jest.fn().mockResolvedValue(false),
}));

beforeEach(() => jest.clearAllMocks());

function okResponse(data: unknown) {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(data),
    text: () => Promise.resolve(JSON.stringify(data)),
  };
}

function errorResponse(status: number) {
  return {
    ok: false,
    status,
    json: () => Promise.reject(new Error('error')),
    text: () => Promise.resolve(`HTTP ${status}`),
  };
}

describe('chat API utils', () => {
  describe('fetchSessions', () => {
    it('세션 목록 조회 (기본 파라미터)', async () => {
      const sessions = { items: [], total: 0 };
      mockFetch.mockResolvedValue(okResponse(sessions));
      const result = await fetchSessions();
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions?limit=50&offset=0',
        expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) }),
      );
      expect(result).toEqual(sessions);
    });

    it('커스텀 limit/offset', async () => {
      mockFetch.mockResolvedValue(okResponse({ items: [], total: 0 }));
      await fetchSessions(10, 5);
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions?limit=10&offset=5',
        expect.anything(),
      );
    });
  });

  describe('createSession', () => {
    it('새 세션 생성', async () => {
      const session = { id: 'abc', title: '새 대화' };
      mockFetch.mockResolvedValue(okResponse(session));
      const result = await createSession();
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions',
        expect.objectContaining({ method: 'POST', body: '{}' }),
      );
      expect(result).toEqual(session);
    });
  });

  describe('fetchMessages', () => {
    it('세션 메시지 목록 조회', async () => {
      const messages = { items: [{ id: 1, content: 'hello' }], total: 1 };
      mockFetch.mockResolvedValue(okResponse(messages));
      const result = await fetchMessages('session-1');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions/session-1/messages?limit=50&offset=0',
        expect.anything(),
      );
      expect(result).toEqual(messages);
    });
  });

  describe('updateSessionTitle', () => {
    it('세션 제목 수정', async () => {
      const updated = { id: 'abc', title: '수정됨' };
      mockFetch.mockResolvedValue(okResponse(updated));
      const result = await updateSessionTitle('abc', '수정됨');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions/abc',
        expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ title: '수정됨' }) }),
      );
      expect(result).toEqual(updated);
    });
  });

  describe('deleteSession', () => {
    it('세션 삭제', async () => {
      mockFetch.mockResolvedValue(okResponse(null));
      await deleteSession('abc');
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/chat/sessions/abc',
        expect.objectContaining({ method: 'DELETE' }),
      );
    });
  });

  describe('authFetch 에러 처리', () => {
    it('401이 아닌 에러 시 throw', async () => {
      mockFetch.mockResolvedValue(errorResponse(500));
      await expect(fetchSessions()).rejects.toThrow('HTTP 500');
    });
  });
});
