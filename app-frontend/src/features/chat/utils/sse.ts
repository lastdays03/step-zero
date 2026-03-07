import type { SSEEvent } from "../types";

export { getAuthHeaders, tryRefreshToken } from "@/lib/sse-auth";

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
