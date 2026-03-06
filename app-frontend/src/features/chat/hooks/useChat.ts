"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { getApiBaseUrl } from "@/lib/env";
import type { ChatMessage, CitationSource, IntentCategory } from "../types";
import { fetchMessages } from "../utils/api";
import {
  getAuthHeaders,
  parseSSELine,
  tryRefreshToken,
} from "../utils/sse";
import { useChatProvider } from "../providers/ChatProvider";

// ------------------------------------------------------------------ //
//  Return 타입
// ------------------------------------------------------------------ //

export interface UseChatReturn {
  messages: ChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  startNewChat: () => void;
}

const AUTO_TITLE_MAX_LENGTH = 40;

function buildAutoTitle(message: string): string {
  const stripped = message.trim();
  if (stripped.length <= AUTO_TITLE_MAX_LENGTH) {
    return stripped;
  }
  return `${stripped.slice(0, AUTO_TITLE_MAX_LENGTH)}…`;
}

// ------------------------------------------------------------------ //
//  Hook
// ------------------------------------------------------------------ //

export function useChat(): UseChatReturn {
  const {
    currentSessionId,
    setCurrentSessionId,
    refreshSessionList,
    publishSessionPreview,
    roadmapContext,
  } = useChatProvider();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  // ---- 마운트/언마운트 ----

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  // ---- 세션 이력 로드 (콜백) ----

  const loadSession = useCallback(
    async (sessionId: string) => {
      abortRef.current?.abort();
      setMessages([]);
      setError(null);
      setIsStreaming(false);
      setIsLoading(true);
      setCurrentSessionId(sessionId);

      try {
        const data = await fetchMessages(sessionId);
        if (!mountedRef.current) return;
        setMessages(data.messages);
      } catch {
        if (!mountedRef.current) return;
        setError("대화 이력을 불러오지 못했습니다.");
      } finally {
        if (mountedRef.current) setIsLoading(false);
      }
    },
    [setCurrentSessionId],
  );

  // ---- 새 대화 시작 ----

  const startNewChat = useCallback(() => {
    abortRef.current?.abort();
    setMessages([]);
    setError(null);
    setIsStreaming(false);
    setCurrentSessionId(null);
  }, [setCurrentSessionId]);

  // ---- SSE 스트리밍 메시지 전송 ----

  const sendMessage = useCallback(
    async (content: string) => {
      const text = content.trim();
      if (!text) return;

      // 진행 중인 스트림 취소
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      // 유저 메시지 추가
      const userMsg: ChatMessage = {
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };
      const previewTimestamp = userMsg.created_at;
      setMessages((prev) => [...prev, userMsg]);
      setError(null);
      setIsStreaming(true);

      // 어시스턴트 플레이스홀더
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "", isStreaming: true },
      ]);

      try {
        const baseUrl = getApiBaseUrl();
        let shouldRefreshSessions = false;
        const body: Record<string, unknown> = { message: text };
        if (currentSessionId) {
          body.session_id = currentSessionId;
        }
        if (roadmapContext?.roadmapId) {
          body.roadmap_id = roadmapContext.roadmapId;
        }

        const doFetch = (headers: Record<string, string>) =>
          fetch(`${baseUrl}/chat/stream`, {
            method: "POST",
            headers,
            body: JSON.stringify(body),
            signal: controller.signal,
          });

        let response = await doFetch(getAuthHeaders());

        // 401 → silent refresh → 1회 재시도
        if (response.status === 401) {
          const refreshed = await tryRefreshToken();
          if (refreshed) {
            response = await doFetch(getAuthHeaders());
          }
        }

        if (!response.ok) {
          const status = response.status;
          if (status === 401)
            throw new Error(
              "인증이 만료되었습니다. 다시 로그인해 주세요.",
            );
          if (status === 403) throw new Error("접근 권한이 없습니다.");
          throw new Error(`서버 오류가 발생했습니다. (${status})`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("스트리밍을 시작할 수 없습니다.");

        const decoder = new TextDecoder();
        let buffer = "";
        let receivedSources: CitationSource[] | undefined;
        let receivedIntent: IntentCategory | undefined;
        let receivedWarning: { code: string; message: string } | undefined;
        let serverMessageId: number | undefined;

        // ---- SSE 이벤트 스트림 파싱 ----

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const event = parseSSELine(line);
            if (!event || !mountedRef.current) continue;

            switch (event.type) {
              case "token":
                setMessages((prev) => {
                  const last = prev[prev.length - 1];
                  if (!last?.isStreaming) return prev;
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...last,
                      content: last.content + (event.token as string),
                    },
                  ];
                });
                break;

              case "meta": {
                const sessionId = event.session_id as string;
                if (sessionId) {
                  const isNewSession = currentSessionId === null;
                  setCurrentSessionId(sessionId);
                  publishSessionPreview({
                    id: sessionId,
                    title: isNewSession ? buildAutoTitle(text) : undefined,
                    message_count: isNewSession ? 1 : undefined,
                    roadmap_id: roadmapContext?.roadmapId ?? undefined,
                    step_id: roadmapContext?.stepId ?? undefined,
                    created_at: isNewSession ? previewTimestamp : undefined,
                    updated_at: previewTimestamp ?? new Date().toISOString(),
                  });
                  shouldRefreshSessions = true;
                }
                if (event.message_id != null)
                  serverMessageId = event.message_id as number;
                if (event.intent)
                  receivedIntent = event.intent as IntentCategory;
                break;
              }

              case "intent":
                receivedIntent = event.category as IntentCategory;
                break;

              case "sources":
                receivedSources = event.sources as CitationSource[];
                break;

              case "warning":
                receivedWarning = {
                  code: (event.code as string) ?? "WARNING",
                  message: event.message as string,
                };
                break;

              case "done":
                setMessages((prev) => {
                  const last = prev[prev.length - 1];
                  if (!last?.isStreaming) return prev;
                  return [
                    ...prev.slice(0, -1),
                    {
                      ...last,
                      id: serverMessageId,
                      isStreaming: false,
                      sources: receivedSources,
                      intent_category: receivedIntent,
                      warning: receivedWarning,
                    },
                  ];
                });
                break;

              case "error":
                setError(event.message as string);
                setMessages((prev) => {
                  const last = prev[prev.length - 1];
                  if (last?.isStreaming && !last.content)
                    return prev.slice(0, -1);
                  if (last?.isStreaming) {
                    return [
                      ...prev.slice(0, -1),
                      { ...last, isStreaming: false },
                    ];
                  }
                  return prev;
                });
                break;
            }
          }
        }

        // 스트리밍 완료 후 최종 정리
        if (mountedRef.current) {
          setMessages((prev) =>
            prev.map((m) =>
              m.isStreaming
                ? {
                    ...m,
                    id: serverMessageId,
                    isStreaming: false,
                    sources: receivedSources,
                    intent_category: receivedIntent,
                    warning: receivedWarning,
                  }
                : m,
            ),
          );
        }
        if (shouldRefreshSessions) {
          refreshSessionList();
        }
      } catch (err: unknown) {
        if (!mountedRef.current) return;
        if (err instanceof DOMException && err.name === "AbortError") return;

        const message =
          err instanceof Error
            ? err.message
            : "AI 응답을 가져오지 못했습니다.";
        setError(message);

        // 빈 플레이스홀더 제거
        setMessages((prev) => {
          const last = prev[prev.length - 1];
          if (last?.isStreaming && !last.content) return prev.slice(0, -1);
          return prev;
        });
      } finally {
        if (mountedRef.current) {
          setIsStreaming(false);
        }
      }
    },
    [
      currentSessionId,
      publishSessionPreview,
      refreshSessionList,
      roadmapContext,
      setCurrentSessionId,
    ],
  );

  return {
    messages,
    isStreaming,
    isLoading,
    error,
    sendMessage,
    loadSession,
    startNewChat,
  };
}
