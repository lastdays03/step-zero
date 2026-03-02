"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient, AUTH_STORAGE_EVENT } from "@/lib/api-client";
import type { StepChatMessage, CitationSource } from "../components/StepChatPanel";

// ---- BE 응답 타입 ----

interface ThreadSummary {
  thread_id: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

interface ChatMessageResponse {
  id: number;
  role: string;
  content: string;
  sources: Record<string, unknown>[] | null;
  created_at: string;
}

// ---- SSE 이벤트 타입 ----

interface SSETokenEvent {
  type: "token";
  token: string;
}

interface SSESourcesEvent {
  type: "sources";
  sources: CitationSource[];
}

interface SSEMetaEvent {
  type: "meta";
  thread_id: string;
  message_id: number;
}

interface SSEDoneEvent {
  type: "done";
}

interface SSEErrorEvent {
  type: "error";
  code: string;
  message: string;
}

type SSEEvent =
  | SSETokenEvent
  | SSESourcesEvent
  | SSEMetaEvent
  | SSEDoneEvent
  | SSEErrorEvent;

// ---- Hook 반환 타입 ----

interface UseStepChatReturn {
  messages: StepChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  threadId: string | null;
  sendMessage: (content: string) => Promise<void>;
  loadHistory: () => Promise<void>;
  clearError: () => void;
}

// ---- API 베이스 URL 추출 ----

function getApiBaseUrl(): string {
  const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
  return (
    explicit ||
    (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1")
  );
}

// ---- Silent Refresh for SSE (native fetch) ----

async function tryRefreshToken(): Promise<string | null> {
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

// ---- Hook ----

export function useStepChat(
  roadmapId: string,
  stepId: number,
): UseStepChatReturn {
  const [messages, setMessages] = useState<StepChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [threadId, setThreadId] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  // 언마운트 시 정리
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  // roadmapId/stepId 변경 시 초기화 + 이력 로드
  useEffect(() => {
    setMessages([]);
    setThreadId(null);
    setError(null);
    void loadHistoryInternal();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [roadmapId, stepId]);

  const loadHistoryInternal = useCallback(async () => {
    if (!roadmapId || !stepId) return;

    setIsLoading(true);
    setError(null);

    try {
      // 1. 스레드 목록 조회
      const threadsRes = await apiClient.get<ThreadSummary[]>(
        `/roadmaps/${roadmapId}/steps/${stepId}/chat/threads`,
      );

      const threads = threadsRes.data;
      if (!threads.length) {
        setIsLoading(false);
        return;
      }

      // 최신 스레드 선택
      const latestThread = threads.sort(
        (a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )[0];

      setThreadId(latestThread.thread_id);

      // 2. 메시지 조회
      const msgsRes = await apiClient.get<ChatMessageResponse[]>(
        `/roadmaps/${roadmapId}/steps/${stepId}/chat/threads/${latestThread.thread_id}/messages`,
        { params: { offset: 0, limit: 50 } },
      );

      if (!mountedRef.current) return;

      const loaded: StepChatMessage[] = msgsRes.data
        .filter((m) => m.role === "user" || m.role === "assistant")
        .map((m) => ({
          id: String(m.id),
          role: m.role as "user" | "assistant",
          content: m.content,
          sources: (m.sources as unknown as CitationSource[]) ?? undefined,
          timestamp: new Date(m.created_at).getTime(),
        }));

      setMessages(loaded);
    } catch {
      if (mountedRef.current) {
        setError("대화 이력을 불러오지 못했습니다.");
      }
    } finally {
      if (mountedRef.current) {
        setIsLoading(false);
      }
    }
  }, [roadmapId, stepId]);

  const sendMessage = useCallback(
    async (content: string) => {
      const trimmed = content.trim();
      if (!trimmed || isStreaming) return;

      // 이전 요청 취소
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      // 유저 메시지 추가
      const userMsg: StepChatMessage = {
        id: `local-${Date.now()}`,
        role: "user",
        content: trimmed,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, userMsg]);
      setIsStreaming(true);
      setError(null);

      // 어시스턴트 스트리밍 메시지 placeholder
      const assistantId = `stream-${Date.now()}`;
      const assistantMsg: StepChatMessage = {
        id: assistantId,
        role: "assistant",
        content: "",
        isStreaming: true,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantMsg]);

      try {
        const baseUrl = getApiBaseUrl();
        const teamId = localStorage.getItem("current_team_id");
        const sseUrl = `${baseUrl}/roadmaps/${roadmapId}/steps/${stepId}/chat/stream`;
        const sseBody = JSON.stringify({
          message: trimmed,
          thread_id: threadId,
        });

        const doFetch = (authToken: string | null) =>
          fetch(sseUrl, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
              ...(teamId ? { "X-Team-Id": teamId } : {}),
            },
            body: sseBody,
            signal: controller.signal,
          });

        const token = localStorage.getItem("token");
        let response = await doFetch(token);

        // 401 시 silent refresh 후 1회 재시도
        if (response.status === 401) {
          const newToken = await tryRefreshToken();
          if (newToken) {
            response = await doFetch(newToken);
          }
        }

        if (!response.ok) {
          const status = response.status;
          if (status === 401) throw new Error("인증이 만료되었습니다. 다시 로그인해 주세요.");
          if (status === 403) throw new Error("접근 권한이 없습니다.");
          if (status === 404) throw new Error("로드맵 또는 단계를 찾을 수 없습니다.");
          throw new Error(`서버 오류가 발생했습니다. (${status})`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("스트리밍을 시작할 수 없습니다.");

        const decoder = new TextDecoder();
        let buffer = "";
        let receivedSources: CitationSource[] | undefined;
        let receivedThreadId: string | null = null;
        let serverMessageId: string | null = null;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            // 하트비트 무시
            if (line.startsWith(": ")) continue;
            if (!line.startsWith("data: ")) continue;

            let event: SSEEvent;
            try {
              event = JSON.parse(line.slice(6)) as SSEEvent;
            } catch {
              continue;
            }

            if (!mountedRef.current) return;

            switch (event.type) {
              case "token":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, content: m.content + event.token }
                      : m,
                  ),
                );
                break;

              case "sources":
                receivedSources = event.sources;
                break;

              case "meta":
                receivedThreadId = event.thread_id;
                serverMessageId = String(event.message_id);
                // 어시스턴트 메시지 ID를 서버 ID로 교체
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, id: serverMessageId! }
                      : m,
                  ),
                );
                break;

              case "done": {
                // 스트리밍 완료 — meta에서 교체된 서버 ID 또는 원래 ID로 탐색
                const targetId = serverMessageId ?? assistantId;
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === targetId
                      ? { ...m, isStreaming: false, sources: receivedSources }
                      : m,
                  ),
                );
                break;
              }

              case "error":
                setError(event.message);
                // 빈 어시스턴트 메시지 제거
                setMessages((prev) => prev.filter((m) => m.id !== assistantId));
                break;
            }
          }
        }

        // 스트리밍 정상 종료 후 최종 정리
        if (mountedRef.current) {
          // done 이벤트에서 이미 처리했으나, 혹시 빠졌을 경우 보장
          setMessages((prev) =>
            prev.map((m) =>
              m.isStreaming
                ? { ...m, isStreaming: false, sources: receivedSources }
                : m,
            ),
          );

          if (receivedThreadId) {
            setThreadId(receivedThreadId);
          }
        }
      } catch (err: unknown) {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;

        const message =
          err instanceof Error ? err.message : "AI 응답을 가져오지 못했습니다.";
        setError(message);

        // 빈 어시스턴트 메시지 제거
        setMessages((prev) =>
          prev.filter((m) => !(m.id === assistantId && !m.content)),
        );
      } finally {
        if (mountedRef.current) {
          setIsStreaming(false);
        }
      }
    },
    [roadmapId, stepId, threadId, isStreaming],
  );

  const clearError = useCallback(() => setError(null), []);

  return {
    messages,
    isStreaming,
    isLoading,
    error,
    threadId,
    sendMessage,
    loadHistory: loadHistoryInternal,
    clearError,
  };
}
