import type {
  ChatSession,
  MessageListResponse,
  SessionListResponse,
} from "../types";
import { getApiBaseUrl, getAuthHeaders, tryRefreshToken } from "./sse";

// ------------------------------------------------------------------ //
//  공통 fetch 래퍼 (401 시 silent refresh 1회 재시도)
// ------------------------------------------------------------------ //

async function authFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path}`;

  let res = await fetch(url, {
    ...init,
    headers: { ...getAuthHeaders(), ...init?.headers },
  });

  if (res.status === 401) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      res = await fetch(url, {
        ...init,
        headers: { ...getAuthHeaders(), ...init?.headers },
      });
    }
  }

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(text || `HTTP ${res.status}`);
  }

  return res;
}

// ------------------------------------------------------------------ //
//  세션 CRUD
// ------------------------------------------------------------------ //

export async function fetchSessions(
  limit = 50,
  offset = 0,
): Promise<SessionListResponse> {
  const res = await authFetch(
    `/chat/sessions?limit=${limit}&offset=${offset}`,
  );
  return res.json() as Promise<SessionListResponse>;
}

export async function createSession(): Promise<ChatSession> {
  const res = await authFetch("/chat/sessions", {
    method: "POST",
    body: JSON.stringify({}),
  });
  return res.json() as Promise<ChatSession>;
}

export async function fetchMessages(
  sessionId: string,
  limit = 50,
  offset = 0,
): Promise<MessageListResponse> {
  const res = await authFetch(
    `/chat/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`,
  );
  return res.json() as Promise<MessageListResponse>;
}

export async function updateSessionTitle(
  sessionId: string,
  title: string,
): Promise<ChatSession> {
  const res = await authFetch(`/chat/sessions/${sessionId}`, {
    method: "PATCH",
    body: JSON.stringify({ title }),
  });
  return res.json() as Promise<ChatSession>;
}

export async function deleteSession(sessionId: string): Promise<void> {
  await authFetch(`/chat/sessions/${sessionId}`, {
    method: "DELETE",
  });
}
