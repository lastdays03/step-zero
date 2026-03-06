import { renderHook, act } from '@testing-library/react';
import { TextEncoder as NodeTextEncoder, TextDecoder as NodeTextDecoder } from 'util';

// jsdom polyfills
global.TextEncoder = NodeTextEncoder as unknown as typeof TextEncoder;
global.TextDecoder = NodeTextDecoder as unknown as typeof TextDecoder;

import { useChat } from '../hooks/useChat';

// ---- Mocks ----

const mockSetCurrentSessionId = jest.fn();

jest.mock('../providers/ChatProvider', () => ({
  useChatProvider: () => ({
    currentSessionId: null,
    setCurrentSessionId: mockSetCurrentSessionId,
    roadmapContext: null,
  }),
}));

jest.mock('../utils/api', () => ({
  fetchMessages: jest.fn(),
}));

jest.mock('../utils/sse', () => ({
  getApiBaseUrl: () => 'http://localhost:8000/api/v1',
  getAuthHeaders: () => ({ Authorization: 'Bearer test', 'Content-Type': 'application/json' }),
  parseSSELine: jest.fn(),
  tryRefreshToken: jest.fn(),
}));

import { fetchMessages } from '../utils/api';
import { parseSSELine, tryRefreshToken } from '../utils/sse';

const mockFetchMessages = fetchMessages as jest.Mock;
const mockParseSSELine = parseSSELine as jest.Mock;
const mockTryRefreshToken = tryRefreshToken as jest.Mock;

// ---- Mock reader 헬퍼 (jsdom에는 ReadableStream/TextEncoder가 없음) ----

function createMockReader(chunks: string[]) {
  const encoder = new TextEncoder();
  let i = 0;
  return {
    read: jest.fn().mockImplementation(() => {
      if (i < chunks.length) {
        return Promise.resolve({ done: false, value: encoder.encode(chunks[i++]) });
      }
      return Promise.resolve({ done: true, value: undefined });
    }),
  };
}

function createMockBody(chunks: string[]) {
  const reader = createMockReader(chunks);
  return { getReader: () => reader };
}

// ---- Setup ----

const originalFetch = global.fetch;

beforeEach(() => {
  jest.clearAllMocks();
  mockSetCurrentSessionId.mockClear();
});

afterEach(() => {
  global.fetch = originalFetch;
});

describe('useChat', () => {
  it('loadSession: 세션 메시지 로드', async () => {
    const msgs = {
      messages: [
        { role: 'user', content: '안녕', created_at: '2026-01-01T00:00:00Z' },
        { role: 'assistant', content: '반갑습니다', created_at: '2026-01-01T00:00:01Z' },
      ],
    };
    mockFetchMessages.mockResolvedValue(msgs);

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.loadSession('sess-1');
    });

    expect(mockSetCurrentSessionId).toHaveBeenCalledWith('sess-1');
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.isLoading).toBe(false);
  });

  it('startNewChat: 상태 초기화', async () => {
    mockFetchMessages.mockResolvedValue({
      messages: [{ role: 'user', content: 'hi' }],
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.loadSession('sess-1');
    });
    expect(result.current.messages).toHaveLength(1);

    act(() => {
      result.current.startNewChat();
    });

    expect(result.current.messages).toHaveLength(0);
    expect(mockSetCurrentSessionId).toHaveBeenCalledWith(null);
  });

  it('sendMessage: SSE 스트리밍으로 어시스턴트 응답 수신', async () => {
    // parseSSELine mock: token → meta → done 순서
    mockParseSSELine
      .mockReturnValueOnce({ type: 'token', token: '안녕' })
      .mockReturnValueOnce({ type: 'meta', session_id: 'sess-new', message_id: 42 })
      .mockReturnValueOnce({ type: 'token', token: '하세요' })
      .mockReturnValueOnce({ type: 'done' });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: createMockBody([
        'data: {"type":"token","token":"안녕"}\n\n',
        'data: {"type":"meta","session_id":"sess-new"}\ndata: {"type":"token","token":"하세요"}\n\n',
        'data: {"type":"done"}\n\n',
      ]),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('질문입니다');
    });

    // 유저 메시지 + 어시스턴트 응답
    expect(result.current.messages).toHaveLength(2);
    expect(result.current.messages[0].role).toBe('user');
    expect(result.current.messages[0].content).toBe('질문입니다');
    expect(result.current.messages[1].role).toBe('assistant');
    expect(result.current.isStreaming).toBe(false);
    expect(mockSetCurrentSessionId).toHaveBeenCalledWith('sess-new');
  });

  it('sendMessage: 빈 메시지는 무시', async () => {
    global.fetch = jest.fn();

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('   ');
    });

    expect(result.current.messages).toHaveLength(0);
    expect(global.fetch).not.toHaveBeenCalled();
  });

  it('sendMessage: 서버 에러 시 에러 상태 설정', async () => {
    global.fetch = jest.fn().mockResolvedValue({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('질문');
    });

    expect(result.current.error).toBe('서버 오류가 발생했습니다. (500)');
    // 유저 메시지만 남고 빈 어시스턴트 플레이스홀더는 제거됨
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.isStreaming).toBe(false);
  });

  it('sendMessage: 401 시 토큰 갱신 후 재시도', async () => {
    mockTryRefreshToken.mockResolvedValue(true);

    mockParseSSELine.mockReturnValueOnce({ type: 'done' });

    global.fetch = jest
      .fn()
      .mockResolvedValueOnce({ ok: false, status: 401 })
      .mockResolvedValueOnce({ ok: true, status: 200, body: createMockBody(['data: done\n\n']) });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('hello');
    });

    expect(mockTryRefreshToken).toHaveBeenCalled();
    expect(global.fetch).toHaveBeenCalledTimes(2);
    expect(result.current.error).toBeNull();
  });

  it('sendMessage: SSE error 이벤트 시 에러 표시', async () => {
    mockParseSSELine
      .mockReturnValueOnce({ type: 'token', token: '일부' })
      .mockReturnValueOnce({ type: 'error', message: 'rate limit exceeded' });

    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      status: 200,
      body: createMockBody([
        'data: {"type":"token","token":"일부"}\n\n',
        'data: {"type":"error","message":"rate limit exceeded"}\n\n',
      ]),
    });

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.sendMessage('질문');
    });

    expect(result.current.error).toBe('rate limit exceeded');
    // 어시스턴트 메시지에 부분 내용이 있으므로 유지됨
    const assistantMsg = result.current.messages.find((m) => m.role === 'assistant');
    expect(assistantMsg).toBeDefined();
    expect(assistantMsg?.isStreaming).toBe(false);
  });

  it('loadSession 실패 시 에러 설정', async () => {
    mockFetchMessages.mockRejectedValue(new Error('fail'));

    const { result } = renderHook(() => useChat());

    await act(async () => {
      await result.current.loadSession('bad-session');
    });

    expect(result.current.error).toBe('대화 이력을 불러오지 못했습니다.');
    expect(result.current.isLoading).toBe(false);
  });
});
