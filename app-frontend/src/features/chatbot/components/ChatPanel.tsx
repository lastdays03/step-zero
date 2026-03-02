"use client";

import type { Ref } from "react";
import { Info, Trash2, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { ChatMessage } from "../types/chat";
import { ChatMessageList } from "./ChatMessageList";
import { ChatInput } from "./ChatInput";

interface ChatPanelProps {
  messages: ChatMessage[];
  isStreaming: boolean;
  isLoading: boolean;
  error: string | null;
  input: string;
  hasCoachContext: boolean;
  stepTitle: string | null;
  onInputChange: (value: string) => void;
  onSend: () => void;
  onClear: () => void;
  onClose: () => void;
  scrollRef: Ref<HTMLDivElement>;
}

export function ChatPanel({
  messages,
  isStreaming,
  isLoading,
  error,
  input,
  hasCoachContext,
  stepTitle,
  onInputChange,
  onSend,
  onClear,
  onClose,
  scrollRef,
}: ChatPanelProps) {
  return (
    <div className="fixed z-50 inset-x-0 bottom-0 h-[70vh] pb-16 md:pb-0 md:inset-x-auto md:right-8 md:bottom-8 md:w-[400px] md:h-[600px] md:max-h-[80vh] flex flex-col bg-slate-50 border border-slate-200 rounded-t-2xl md:rounded-2xl shadow-2xl animate-in slide-in-from-bottom duration-300">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white rounded-t-2xl md:rounded-t-2xl">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center">
            <span className="text-[10px] text-white font-bold">AI</span>
          </div>
          <div className="min-w-0">
            <h3 className="text-sm font-bold text-slate-800">
              {hasCoachContext ? "AI 코치" : "AI 어시스턴트"}
            </h3>
            {hasCoachContext && stepTitle && (
              <p className="text-[11px] text-slate-500 truncate">
                {stepTitle}
              </p>
            )}
          </div>
        </div>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            onClick={onClear}
            className="h-8 w-8 text-slate-400 hover:text-slate-600"
            title="대화 초기화"
          >
            <Trash2 className="w-4 h-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 text-slate-400 hover:text-slate-600"
            title="닫기"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Messages */}
      <ChatMessageList
        messages={messages}
        isStreaming={isStreaming}
        isLoading={isLoading}
        hasCoachContext={hasCoachContext}
        scrollRef={scrollRef}
      />

      {/* Error */}
      {error && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-t border-red-100">
          {error}
        </div>
      )}

      {/* 면책 고지 */}
      <div className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100 bg-slate-50/80">
        <Info className="w-3 h-3 inline mr-1 -mt-0.5" />
        AI가 생성한 정보이며, 정확성을 보장하지 않습니다. 중요한 결정은 전문가와
        상담하세요.
      </div>

      {/* Input */}
      <ChatInput
        value={input}
        onChange={onInputChange}
        onSend={onSend}
        isLoading={isStreaming}
      />
    </div>
  );
}
