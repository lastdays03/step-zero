import { getApiBaseUrl, getAuthHeaders, parseSSELine } from '../utils/sse';

describe('getApiBaseUrl', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('NEXT_PUBLIC_API_BASE_URL 우선 사용', () => {
    process.env.NEXT_PUBLIC_API_BASE_URL = 'https://api.example.com/api/v1';
    process.env.NEXT_PUBLIC_API_URL = 'https://other.com';
    expect(getApiBaseUrl()).toBe('https://api.example.com/api/v1');
  });

  it('NEXT_PUBLIC_API_URL로 폴백 (/api/v1 추가)', () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    process.env.NEXT_PUBLIC_API_URL = 'https://api.example.com/';
    expect(getApiBaseUrl()).toBe('https://api.example.com/api/v1');
  });

  it('둘 다 없으면 localhost 기본값', () => {
    delete process.env.NEXT_PUBLIC_API_BASE_URL;
    delete process.env.NEXT_PUBLIC_API_URL;
    expect(getApiBaseUrl()).toBe('http://localhost:8000/api/v1');
  });
});

describe('getAuthHeaders', () => {
  beforeEach(() => localStorage.clear());

  it('토큰 없으면 Content-Type만', () => {
    const headers = getAuthHeaders();
    expect(headers).toEqual({ 'Content-Type': 'application/json' });
    expect(headers).not.toHaveProperty('Authorization');
  });

  it('토큰 있으면 Authorization 추가', () => {
    localStorage.setItem('token', 'my-jwt');
    const headers = getAuthHeaders();
    expect(headers.Authorization).toBe('Bearer my-jwt');
  });

  it('팀 ID 있으면 X-Team-Id 추가', () => {
    localStorage.setItem('token', 'jwt');
    localStorage.setItem('current_team_id', '42');
    const headers = getAuthHeaders();
    expect(headers['X-Team-Id']).toBe('42');
  });
});

describe('parseSSELine', () => {
  it('data: JSON 파싱', () => {
    const event = parseSSELine('data: {"type":"token","content":"hello"}');
    expect(event).toEqual({ type: 'token', content: 'hello' });
  });

  it('SSE 주석 무시', () => {
    expect(parseSSELine(': keep-alive')).toBeNull();
  });

  it('data: 프리픽스 없는 줄 무시', () => {
    expect(parseSSELine('event: message')).toBeNull();
  });

  it('잘못된 JSON은 null 반환', () => {
    expect(parseSSELine('data: {invalid json')).toBeNull();
  });

  it('빈 줄은 null 반환', () => {
    expect(parseSSELine('')).toBeNull();
  });
});
