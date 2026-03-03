"use client";

import {
  Info,
  Menu,
  Plus,
  X,
  MapPin,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { useChatProvider } from "../providers/ChatProvider";
import { useChat } from "../hooks/useChat";
import { ChatMessages } from "./ChatMessages";
import { ChatInput } from "./ChatInput";
import { ChatHistory } from "./ChatHistory";

export function ChatPanel() {
  const {
    closePanel,
    isHistoryView,
    setHistoryView,
    roadmapContext,
    hasRoadmapContext,
  } = useChatProvider();

  const {
    messages,
    isStreaming,
    isLoading,
    error,
    sendMessage,
    loadSession,
    startNewChat,
  } = useChat();

  return (
    <div className="fixed z-50 inset-x-0 bottom-0 h-[70vh] pb-16 md:pb-0 md:inset-x-auto md:right-8 md:bottom-8 md:w-[420px] md:h-[620px] md:max-h-[80vh] flex flex-col bg-slate-50 border border-slate-200 rounded-t-2xl md:rounded-2xl shadow-2xl animate-in slide-in-from-bottom duration-300">
      {/* ---- 헤더 ---- */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-white rounded-t-2xl">
        <div className="flex items-center gap-2.5">
          {/* 히스토리 토글 */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setHistoryView(!isHistoryView)}
            className="h-8 w-8 text-slate-400 hover:text-slate-600"
            title="대화 이력"
          >
            <Menu className="w-4 h-4" />
          </Button>

          {/* 타이틀 */}
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-full bg-gradient-to-tr from-blue-500 to-purple-400 flex items-center justify-center">
              <span className="text-[10px] text-white font-bold">AI</span>
            </div>
            <h3 className="text-sm font-bold text-slate-800">StepZero AI</h3>
          </div>
        </div>

        <div className="flex items-center gap-1">
          {/* 새 대화 */}
          <Button
            variant="ghost"
            size="icon"
            onClick={() => {
              startNewChat();
              setHistoryView(false);
            }}
            className="h-8 w-8 text-slate-400 hover:text-slate-600"
            title="새 대화"
          >
            <Plus className="w-4 h-4" />
          </Button>

          {/* 닫기 */}
          <Button
            variant="ghost"
            size="icon"
            onClick={closePanel}
            className="h-8 w-8 text-slate-400 hover:text-slate-600"
            title="닫기"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* ---- 서브헤더: 로드맵 컨텍스트 ---- */}
      {hasRoadmapContext && roadmapContext?.stepTitle && !isHistoryView && (
        <div className="flex items-center gap-1.5 px-4 py-2 bg-blue-50 border-b border-blue-100 text-xs text-blue-700">
          <MapPin className="w-3 h-3 shrink-0" />
          <span className="truncate font-medium">
            {roadmapContext.stepTitle}
          </span>
        </div>
      )}

      {/* ---- 본문: 슬라이드 전환 ---- */}
      <div className="flex-1 overflow-hidden relative">
        {/* 대화 뷰 */}
        <div
          className={`absolute inset-0 flex flex-col transition-transform duration-200 ease-out ${
            isHistoryView ? "-translate-x-full" : "translate-x-0"
          }`}
        >
          <ChatMessages
            messages={messages}
            isStreaming={isStreaming}
            isLoading={isLoading}
            onSendMessage={sendMessage}
          />
        </div>

        {/* 히스토리 뷰 */}
        <div
          className={`absolute inset-0 flex flex-col transition-transform duration-200 ease-out ${
            isHistoryView ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <ChatHistory
            onClose={() => setHistoryView(false)}
            onSelectSession={(sessionId) => {
              loadSession(sessionId);
              setHistoryView(false);
            }}
          />
        </div>
      </div>

      {/* ---- 에러 ---- */}
      {error && !isHistoryView && (
        <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-t border-red-100">
          {error}
        </div>
      )}

      {/* ---- 면책 고지 ---- */}
      {!isHistoryView && (
        <div className="px-4 py-2 text-[11px] text-slate-400 border-t border-slate-100 bg-slate-50/80">
          <Info className="w-3 h-3 inline mr-1 -mt-0.5" />
          AI가 생성한 정보이며, 정확성을 보장하지 않습니다. 중요한 결정은
          전문가와 상담하세요.
        </div>
      )}

      {/* ---- 입력 ---- */}
      {!isHistoryView && (
        <ChatInput onSend={sendMessage} isStreaming={isStreaming} />
      )}
    </div>
  );
}
