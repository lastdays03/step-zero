"use client";

import type { Ref } from "react";
import { Bot, Loader2, MessageSquare } from "lucide-react";
import type { ChatMessage } from "../types/chat";
import { ChatBubble } from "./ChatBubble";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  hasCoachContext: boolean;
  scrollRef: Ref<HTMLDivElement>;
}

export function ChatMessageList({
  messages,
  isStreaming,
  isLoading,
  hasCoachContext,
  scrollRef,
}: ChatMessageListProps) {
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

      {/* 빈 상태 */}
      {messages.length === 0 && !isStreaming && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-center text-slate-400 gap-3">
          {hasCoachContext ? (
            <>
              <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-[#36a4f2]/10 to-purple-100 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-[#36a4f2]" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-600">
                  현재 단계에 대해 물어보세요
                </p>
                <p className="text-xs text-slate-400 mt-1">
                  체크리스트, 필요 서류, 관련 법령 등
                  <br />
                  단계 진행에 필요한 정보를 안내해 드려요
                </p>
              </div>
            </>
          ) : (
            <>
              <Bot className="w-8 h-8" />
              <p className="text-sm">무엇이든 물어보세요!</p>
              <p className="text-xs">법률/행정 질문도 가능합니다</p>
            </>
          )}
        </div>
      )}

      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}

      {/* 스트리밍 대기 인디케이터 (토큰 도착 전) */}
      {isStreaming &&
        messages.length > 0 &&
        !messages[messages.length - 1]?.isStreaming &&
        messages[messages.length - 1]?.role === "user" && (
          <div className="flex gap-2 items-start">
            <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0 mt-0.5">
              <Bot className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="rounded-xl rounded-tl-none border border-slate-200 bg-white px-4 py-3">
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
