"use client";

import type { Ref } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ChatMessage } from "../types/chat";
import { ChatMessageList } from "./ChatMessageList";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  messages: ChatMessage[];
  isLoading: boolean;
  error: string | null;
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onClear: () => void;
  scrollRef: Ref<HTMLDivElement>;
}

export function ChatPanel({
  messages,
  isLoading,
  error,
  input,
  onInputChange,
  onSend,
  onClear,
  scrollRef,
}: ChatPanelProps) {
  return (
    <div className="fixed z-50 inset-x-0 bottom-0 h-[70vh] pb-28 md:pb-0 md:inset-x-auto md:right-8 md:bottom-20 md:w-[400px] md:h-[600px] md:max-h-[80vh] flex flex-col bg-slate-50 border border-slate-200 rounded-t-2xl md:rounded-2xl shadow-2xl animate-in slide-in-from-bottom duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white rounded-t-2xl md:rounded-t-2xl">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center">
            <span className="text-[10px] text-white font-bold">AI</span>
          </div>
          <h3 className="text-sm font-bold text-slate-800">AI 어시스턴트</h3>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onClear}
          className="h-8 w-8 text-slate-400 hover:text-slate-600"
          title="대화 초기화"
        >
          <Trash2 className="w-4 h-4" />
        </Button>
      </div>

      {/* Messages */}
      <ChatMessageList
        messages={messages}
        isLoading={isLoading}
        scrollRef={scrollRef}
      />

      {/* Error */}
      {error && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-t border-red-100">
          {error}
        </div>
      )}

      {/* Input */}
      <ChatInput
        value={input}
        onChange={onInputChange}
        onSend={onSend}
        isLoading={isLoading}
      />
    </div>
  );
}
