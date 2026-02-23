"use client";

import type { Ref } from "react";
import { Bot } from "lucide-react";
import type { ChatMessage } from "../types/chat";
import { ChatBubble } from "./ChatBubble";

interface ChatMessageListProps {
  messages: ChatMessage[];
  isLoading: boolean;
  scrollRef: Ref<HTMLDivElement>;
}

export function ChatMessageList({ messages, isLoading, scrollRef }: ChatMessageListProps) {
  return (
    <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      {messages.length === 0 && !isLoading && (
        <div className="flex flex-col items-center justify-center h-full text-center text-slate-400 gap-2">
          <Bot className="w-8 h-8" />
          <p className="text-sm">무엇이든 물어보세요!</p>
          <p className="text-xs">법률/행정 질문도 가능합니다</p>
        </div>
      )}
      {messages.map((msg) => (
        <ChatBubble key={msg.id} message={msg} />
      ))}
      {isLoading && (
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
