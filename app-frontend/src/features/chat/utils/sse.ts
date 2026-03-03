import { AUTH_STORAGE_EVENT } from "@/lib/api-client";
import type { SSEEvent } from "../types";

// ------------------------------------------------------------------ //
//  API 베이스 URL
// ------------------------------------------------------------------ //

export function getApiBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  return (
    explicit ||
    (apiUrl
      ? `${apiUrl.replace(/\/$/, "")}/api/v1`
      : "http://localhost:8000/api/v1")
  );
}

// ------------------------------------------------------------------ //
//  인증 헤더
// ------------------------------------------------------------------ //

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

// ------------------------------------------------------------------ //
//  Silent Refresh (native fetch — SSE용)
// ------------------------------------------------------------------ //

export async function tryRefreshToken(): Promise<boolean> {
  const refreshToken = localStorage.getItem("refresh_token");
  if (!refreshToken) return false;

  try {
    const baseUrl = getApiBaseUrl();
    const res = await fetch(`${baseUrl}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!res.ok) return false;

    const data = (await res.json()) as {
      access_token: string;
      refresh_token: string;
    };

    localStorage.setItem("token", data.access_token);
    localStorage.setItem("refresh_token", data.refresh_token);
    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));

    return true;
  } catch {
    return false;
  }
}

// ------------------------------------------------------------------ //
//  SSE 라인 파서
// ------------------------------------------------------------------ //

export function parseSSELine(line: string): SSEEvent | null {
  if (line.startsWith(": ")) return null;
  if (!line.startsWith("data: ")) return null;

  try {
    return JSON.parse(line.slice(6)) as SSEEvent;
  } catch {
    return null;
  }
}
