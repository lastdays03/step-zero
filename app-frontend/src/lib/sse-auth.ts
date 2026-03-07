import { AUTH_STORAGE_EVENT } from "@/lib/api-client";
import { getApiBaseUrl } from "@/lib/env";

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
