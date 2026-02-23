"use client";

import { useCallback, useRef, useState } from "react";
import { apiClient } from "@/lib/api-client";
import type { ChatMessage } from "../types/chat";

interface ChatApiResponse {
  answer: string;
  source: "legal_rag" | "general";
}

export function useChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, []);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || isLoading) return;

    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: text,
      timestamp: Date.now(),
    };

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setError(null);
    setIsLoading(true);
    scrollToBottom();

    try {
      const res = await apiClient.post<ChatApiResponse>("/rag/chat", {
        message: text,
      });

      const assistantMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: res.data.answer,
        source: res.data.source,
        timestamp: Date.now(),
      };

      setMessages((prev) => [...prev, assistantMsg]);
    } catch {
      setError("AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
      scrollToBottom();
    }
  }, [input, isLoading, scrollToBottom]);

  const togglePanel = useCallback(() => {
    setIsOpen((prev) => !prev);
  }, []);

  const clearHistory = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return {
    messages,
    isOpen,
    isLoading,
    error,
    input,
    setInput,
    sendMessage,
    togglePanel,
    clearHistory,
    scrollRef,
  };
}
