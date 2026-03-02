import { AUTH_STORAGE_EVENT } from "@/lib/api-client";

// ---- SSE 이벤트 타입 ----

export interface SSETokenEvent {
  type: "token";
  token: string;
}

export interface SSESourcesEvent {
  type: "sources";
  sources: { id: number; type: "legal_basis" | "document"; title: string; url?: string }[];
}

export interface SSEMetaEvent {
  type: "meta";
  thread_id: string;
  message_id: number;
}

export interface SSEDoneEvent {
  type: "done";
}

export interface SSEErrorEvent {
  type: "error";
  code: string;
  message: string;
}

export type SSEEvent =
  | SSETokenEvent
  | SSESourcesEvent
  | SSEMetaEvent
  | SSEDoneEvent
  | SSEErrorEvent;

// ---- API 베이스 URL ----

export function getApiBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  return (
    explicit ||
    (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1")
  );
}

// ---- 인증 헤더 ----

export function getAuthHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = localStorage.getItem("token");
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const teamId = localStorage.getItem("current_team_id");
  if (teamId) {
    headers["X-Team-Id"] = teamId;
  }

  return headers;
}

// ---- Silent Refresh for SSE (native fetch) ----

export async function tryRefreshToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return null;

  try {
    const baseUrl = getApiBaseUrl();
    const res = await fetch(`${baseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) return null;

    const data = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));

    return data.access_token;
  } catch {
    return null;
  }
}

// ---- SSE 라인 파서 ----

export function parseSSELine(line: string): SSEEvent | null {
  // 하트비트 무시
  if (line.startsWith(": ")) return null;
  if (!line.startsWith("data: ")) return null;

  try {
    return JSON.parse(line.slice(6)) as SSEEvent;
  } catch {
    return null;
  }
}
