"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ChatMessage, CitationSource } from "../types/chat";
import {
  getApiBaseUrl,
  getAuthHeaders,
  tryRefreshToken,
  parseSSELine,
} from "../utils/sseClient";
import { useChatContext } from "../providers/ChatContextProvider";

// ---- BE 응답 타입 (코치 이력 로드) ----

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

// ---- Hook ----

export function useChatbot() {
  const {
    roadmapId,
    stepId,
    stepTitle,
    hasCoachContext,
    isPanelOpen: isOpen,
    togglePanel,
    closePanel,
  } = useChatContext();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [threadId, setThreadId] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const mountedRef = useRef(true);

  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
      abortRef.current?.abort();
    };
  }, []);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, []);

  // 코치 컨텍스트 변경 시 대화 초기화 + 이력 로드
  useEffect(() => {
    setMessages([]);
    setThreadId(null);
    setError(null);

    if (hasCoachContext && roadmapId && stepId) {
      void loadHistory(roadmapId, stepId);
    }
  }, [roadmapId, stepId, hasCoachContext]);

  // ---- 코치 모드 이력 로드 ----

  async function loadHistory(rmId: string, sId: number) {
    if (!mountedRef.current) return;
    setIsLoading(true);
    setError(null);

    try {
      const threadsRes = await apiClient.get<ThreadSummary[]>(
        `/roadmaps/${rmId}/steps/${sId}/chat/threads`,
      );

      const threads = threadsRes.data;
      if (!threads.length) {
        if (mountedRef.current) setIsLoading(false);
        return;
      }

      const latestThread = threads.sort(
        (a, b) =>
          new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
      )[0];

      setThreadId(latestThread.thread_id);

      const msgsRes = await apiClient.get<ChatMessageResponse[]>(
        `/roadmaps/${rmId}/steps/${sId}/chat/threads/${latestThread.thread_id}/messages`,
        { params: { offset: 0, limit: 50 } },
      );

      if (!mountedRef.current) return;

      const loaded: ChatMessage[] = msgsRes.data
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
  }

  // ---- SSE 스트리밍 메시지 전송 ----

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isStreaming) return;

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    const userMsg: ChatMessage = {
      id: `local-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError(null);
    setIsStreaming(true);
    scrollToBottom();

    const assistantId = `stream-${Date.now()}`;
    const assistantMsg: ChatMessage = {
      id: assistantId,
      role: "assistant",
      content: "",
      isStreaming: true,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, assistantMsg]);

    try {
      const baseUrl = getApiBaseUrl();
      const sseUrl = `${baseUrl}/rag/chat/stream`;

      const body: Record<string, unknown> = { message: text };
      if (hasCoachContext && roadmapId && stepId) {
        body.roadmap_id = roadmapId;
        body.step_id = stepId;
        if (threadId) body.thread_id = threadId;
      }

      const doFetch = (headers: Record<string, string>) =>
        fetch(sseUrl, {
          method: "POST",
          headers,
          body: JSON.stringify(body),
          signal: controller.signal,
        });

      let response = await doFetch(getAuthHeaders());

      // 401 → silent refresh → 1회 재시도
      if (response.status === 401) {
        const newToken = await tryRefreshToken();
        if (newToken) {
          const retryHeaders = getAuthHeaders();
          response = await doFetch(retryHeaders);
        }
      }

      if (!response.ok) {
        const status = response.status;
        if (status === 401)
          throw new Error("인증이 만료되었습니다. 다시 로그인해 주세요.");
        if (status === 403) throw new Error("접근 권한이 없습니다.");
        if (status === 404)
          throw new Error("요청한 리소스를 찾을 수 없습니다.");
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
          const event = parseSSELine(line);
          if (!event) continue;
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
              scrollToBottom();
              break;

            case "sources":
              receivedSources = event.sources as CitationSource[];
              break;

            case "meta":
              receivedThreadId = event.thread_id;
              serverMessageId = String(event.message_id);
              setMessages((prev) =>
                prev.map((m) =>
                  m.id === assistantId
                    ? { ...m, id: serverMessageId! }
                    : m,
                ),
              );
              break;

            case "done": {
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
              setMessages((prev) =>
                prev.filter((m) => m.id !== assistantId),
              );
              break;
          }
        }
      }

      // 스트리밍 완료 후 최종 정리
      if (mountedRef.current) {
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
        err instanceof Error
          ? err.message
          : "AI 응답을 가져오지 못했습니다.";
      setError(message);

      setMessages((prev) =>
        prev.filter((m) => !(m.id === assistantId && !m.content)),
      );
    } finally {
      if (mountedRef.current) {
        setIsStreaming(false);
        scrollToBottom();
      }
    }
  }, [
    input,
    isStreaming,
    scrollToBottom,
    hasCoachContext,
    roadmapId,
    stepId,
    threadId,
  ]);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setThreadId(null);
    setError(null);
  }, []);

  return {
    messages,
    isOpen,
    isStreaming,
    isLoading,
    error,
    input,
    setInput,
    sendMessage,
    togglePanel,
    closePanel,
    clearHistory,
    scrollRef,
    hasCoachContext,
    stepTitle,
  };
}
