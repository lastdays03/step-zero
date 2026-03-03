"use client";

import { useCallback, useEffect, useRef } from "react";
import { Bot, Loader2 } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "../types";
import { ChatMessage } from "./ChatMessage";
import { ChatEmptyState } from "./ChatEmptyState";

interface ChatMessagesProps {
  messages: ChatMessageType[];
  isStreaming: boolean;
  isLoading: boolean;
  onSendMessage?: (message: string) => void;
}

export function ChatMessages({
  messages,
  isStreaming,
  isLoading,
  onSendMessage,
}: ChatMessagesProps) {
  const scrollRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: "smooth",
      });
    });
  }, []);

  // 메시지 변경 시 자동 스크롤
  useEffect(() => {
    scrollToBottom();
  }, [messages.length, scrollToBottom]);

  // 스트리밍 중 마지막 메시지 업데이트 시 스크롤
  const lastMsg = messages[messages.length - 1];
  useEffect(() => {
    if (lastMsg?.isStreaming) {
      scrollToBottom();
    }
  }, [lastMsg?.content, lastMsg?.isStreaming, scrollToBottom]);

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-3 space-y-3"
    >
      {/* 이력 로딩 */}
      {isLoading && messages.length === 0 && (
        <div className="flex flex-col items-center justify-center h-full text-slate-400 gap-2">
          <Loader2 className="w-6 h-6 animate-spin" />
          <p className="text-xs">대화 이력 불러오는 중...</p>
        </div>
      )}

      {/* 빈 상태 — ChatEmptyState (추천 질문 포함) */}
      {messages.length === 0 && !isStreaming && !isLoading && onSendMessage && (
        <ChatEmptyState onSendMessage={onSendMessage} />
      )}

      {/* 메시지 목록 */}
      {messages.map((msg, idx) => (
        <ChatMessage key={msg.id ?? `msg-${idx}`} message={msg} />
      ))}

      {/* 스트리밍 대기 인디케이터 (AI 플레이스홀더 도착 전) */}
      {isStreaming &&
        messages.length > 0 &&
        !messages[messages.length - 1]?.isStreaming &&
        messages[messages.length - 1]?.role === "user" && (
          <div className="flex gap-2.5 items-start">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-500 to-purple-400 flex items-center justify-center shrink-0 mt-0.5">
              <Bot className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-3">
              <div className="flex gap-1">
                <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce [animation-delay:0ms]" />
                <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce [animation-delay:150ms]" />
                <span className="w-2 h-2 rounded-full bg-slate-300 animate-bounce [animation-delay:300ms]" />
              </div>
            </div>
          </div>
        )}
    </div>
  );
}
