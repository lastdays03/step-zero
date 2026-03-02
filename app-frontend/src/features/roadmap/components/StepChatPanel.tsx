"use client";

import { useState, useRef, useEffect, useCallback, type ReactNode } from "react";
import { X, Send, Loader2, MessageSquare, Info, Bot, Gavel, FileText, ChevronDown, ChevronUp, ExternalLink } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useStepChat } from "../hooks/useStepChat";

// ---- Types ----

export interface StepChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: CitationSource[];
  isStreaming?: boolean;
  timestamp: number;
}

export interface CitationSource {
  id: number;
  type: "legal_basis" | "document";
  title: string;
  url?: string;
}

// ---- Props ----

interface StepChatPanelProps {
  roadmapId: string;
  stepId: number;
  stepTitle: string;
  isOpen: boolean;
  onClose: () => void;
}

// ---- Component ----

export function StepChatPanel({
  roadmapId,
  stepId,
  stepTitle,
  isOpen,
  onClose,
}: StepChatPanelProps) {
  const {
    messages,
    isStreaming,
    isLoading,
    error,
    sendMessage,
    clearError,
  } = useStepChat(roadmapId, stepId);

  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  // 자동 스크롤
  useEffect(() => {
    const el = scrollRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  // 패널 열릴 때 입력에 포커스
  useEffect(() => {
    if (isOpen) {
      const timer = setTimeout(() => textareaRef.current?.focus(), 300);
      return () => clearTimeout(timer);
    }
  }, [isOpen]);

  // textarea 높이 자동 조절
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [input]);

  // ESC 키로 패널 닫기
  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [isOpen, onClose]);

  // 모바일: 바디 스크롤 잠금
  useEffect(() => {
    if (!isOpen) return;
    const original = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = original;
    };
  }, [isOpen]);

  // 모바일: 키보드 올라올 때 입력 영역 가시성 확보
  useEffect(() => {
    if (!isOpen) return;
    const vv = window.visualViewport;
    if (!vv) return;

    const handleResize = () => {
      const panel = panelRef.current;
      if (!panel) return;
      const keyboardOffset = window.innerHeight - vv.height;
      panel.style.paddingBottom = keyboardOffset > 0 ? `${keyboardOffset}px` : "0px";
    };

    vv.addEventListener("resize", handleResize);
    return () => vv.removeEventListener("resize", handleResize);
  }, [isOpen]);

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;

    setInput("");
    clearError();
    void sendMessage(trimmed);
  }, [input, isStreaming, sendMessage, clearError]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 백드롭 오버레이 */}
      <div
        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-[2px] animate-in fade-in duration-200"
        onClick={onClose}
      />

      {/* 패널 */}
      <div
        ref={panelRef}
        className={cn(
          "fixed z-50 flex flex-col bg-white shadow-2xl",
          // 모바일: 하단 시트
          "inset-x-0 bottom-0 h-[85vh] rounded-t-2xl",
          // 데스크톱: 우측 슬라이드아웃
          "md:inset-x-auto md:right-4 md:top-20 md:bottom-4 md:w-[420px] md:h-auto md:rounded-2xl",
          // 애니메이션
          "animate-in slide-in-from-bottom md:slide-in-from-right duration-300",
        )}
      >
        {/* 모바일 드래그 핸들 */}
        <div className="flex justify-center pt-2 pb-0 md:hidden">
          <div className="w-10 h-1 rounded-full bg-slate-300" />
        </div>

        {/* 헤더 */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-gradient-to-r from-[#36a4f2]/5 to-purple-50 rounded-t-2xl md:rounded-t-2xl">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0">
              <MessageSquare className="w-4 h-4 text-white" />
            </div>
            <div className="min-w-0">
              <h3 className="text-sm font-bold text-slate-800 truncate">
                AI 코치
              </h3>
              <p className="text-[11px] text-slate-500 truncate">
                {stepTitle}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={onClose}
            className="h-8 w-8 text-slate-400 hover:text-slate-600 shrink-0"
            title="닫기"
          >
            <X className="w-4 h-4" />
          </Button>
        </div>

        {/* 메시지 영역 */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto px-4 py-3 space-y-3">
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
              <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-[#36a4f2]/10 to-purple-100 flex items-center justify-center">
                <MessageSquare className="w-6 h-6 text-[#36a4f2]" />
              </div>
              <div>
                <p className="text-sm font-medium text-slate-600">이 단계에 대해 물어보세요</p>
                <p className="text-xs text-slate-400 mt-1">
                  체크리스트, 필요 서류, 관련 법령 등<br />
                  단계 진행에 필요한 정보를 안내해 드려요
                </p>
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} />
          ))}

          {/* 스트리밍 대기 인디케이터 (토큰 도착 전) */}
          {isStreaming && messages.length > 0 && !messages[messages.length - 1]?.isStreaming && messages[messages.length - 1]?.role === "user" && (
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

        {/* 에러 */}
        {error && (
          <div className="px-4 py-2 text-xs text-red-600 bg-red-50 border-t border-red-100">
            {error}
          </div>
        )}

        {/* 면책 고정 문구 */}
        <div className="px-4 py-2 text-xs text-slate-400 border-t border-slate-100 bg-slate-50/80">
          <Info className="w-3 h-3 inline mr-1 -mt-0.5" />
          AI가 생성한 정보이며, 정확성을 보장하지 않습니다. 중요한 결정은 전문가와 상담하세요.
        </div>

        {/* 입력 영역 */}
        <div className="border-t border-slate-200 px-3 py-2 pb-[calc(0.5rem+env(safe-area-inset-bottom,0px))] md:pb-2 bg-white rounded-b-none md:rounded-b-2xl">
          <div className="flex items-end gap-2">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="이 단계에 대해 질문하세요..."
              rows={1}
              disabled={isStreaming}
              className="flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-[#36a4f2] disabled:opacity-50 max-h-[120px]"
            />
            <Button
              onClick={handleSend}
              disabled={isStreaming || !input.trim()}
              size="icon"
              className="h-9 w-9 shrink-0 rounded-lg bg-[#36a4f2] hover:bg-[#2b83c2] disabled:opacity-50"
            >
              {isStreaming ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}

// ---- 출처 인용 파싱 ----

const CITATION_REGEX = /\[(법령|서류)\s*(\d+)\]/g;

function renderCitationLine(
  line: string,
  keyPrefix: string,
  sources?: CitationSource[],
): ReactNode[] {
  if (!sources?.length) {
    return [<span key={`${keyPrefix}-text`}>{line}</span>];
  }

  const parts: ReactNode[] = [];
  let lastIndex = 0;
  let match: RegExpExecArray | null;

  const regex = new RegExp(CITATION_REGEX.source, "g");
  while ((match = regex.exec(line)) !== null) {
    // 매치 앞 텍스트
    if (match.index > lastIndex) {
      parts.push(
        <span key={`${keyPrefix}-t-${lastIndex}`}>
          {line.slice(lastIndex, match.index)}
        </span>,
      );
    }

    const citationType = match[1]; // "법령" or "서류"
    const citationNum = parseInt(match[2], 10);
    const sourceType = citationType === "법령" ? "legal_basis" : "document";
    const matchedSource = sources.find(
      (s) => s.type === sourceType && s.id === citationNum,
    );

    parts.push(
      <span
        key={`${keyPrefix}-c-${match.index}`}
        className="inline-flex items-center gap-0.5 px-1 py-0.5 rounded bg-[#36a4f2]/10 text-[#36a4f2] text-xs font-medium cursor-default"
        title={matchedSource?.title ?? `${citationType} ${citationNum}`}
      >
        {citationType === "법령" ? (
          <Gavel className="w-3 h-3" />
        ) : (
          <FileText className="w-3 h-3" />
        )}
        {match[0]}
      </span>,
    );

    lastIndex = match.index + match[0].length;
  }

  // 남은 텍스트
  if (lastIndex < line.length) {
    parts.push(
      <span key={`${keyPrefix}-t-${lastIndex}`}>{line.slice(lastIndex)}</span>,
    );
  }

  return parts.length ? parts : [<span key={`${keyPrefix}-text`}>{line}</span>];
}

// ---- 출처 카드 ----

function SourcesCard({ sources }: { sources: CitationSource[] }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-2 pt-2 border-t border-slate-100">
      <button
        type="button"
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-1 text-xs font-medium text-slate-500 hover:text-[#36a4f2] transition-colors"
      >
        {expanded ? (
          <ChevronUp className="w-3 h-3" />
        ) : (
          <ChevronDown className="w-3 h-3" />
        )}
        출처 {sources.length}건
      </button>
      {expanded && (
        <ul className="mt-1.5 space-y-1">
          {sources.map((src) => (
            <li
              key={`${src.type}-${src.id}`}
              className="flex items-start gap-2 px-2 py-1.5 rounded-md bg-slate-50 text-xs"
            >
              {src.type === "legal_basis" ? (
                <Gavel className="w-3.5 h-3.5 text-amber-600 shrink-0 mt-0.5" />
              ) : (
                <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0 mt-0.5" />
              )}
              <div className="min-w-0">
                <p className="font-medium text-slate-700 truncate">
                  [{src.type === "legal_basis" ? "법령" : "서류"} {src.id}] {src.title}
                </p>
                {src.url && (
                  <a
                    href={src.url}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-0.5 mt-0.5 text-[#36a4f2] hover:underline"
                  >
                    원문 보기 <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

// ---- 채팅 버블 ----

function ChatBubble({ message }: { message: StepChatMessage }) {
  if (message.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-xl rounded-tr-none bg-[#36a4f2] px-4 py-2.5 text-sm text-white whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  const hasSources = !message.isStreaming && message.sources && message.sources.length > 0;

  return (
    <div className="flex gap-2 items-start">
      <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="max-w-[85%] rounded-xl rounded-tl-none border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700">
        {message.content
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line, idx) => (
            <p key={`msg-${message.id}-${idx}`} className="mb-1.5 last:mb-0 leading-relaxed">
              {renderCitationLine(line, `msg-${message.id}-${idx}`, message.sources)}
            </p>
          ))}
        {/* 스트리밍 중 커서 */}
        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-[#36a4f2] animate-pulse ml-0.5 -mb-0.5" />
        )}
        {/* 출처 카드 */}
        {hasSources && <SourcesCard sources={message.sources!} />}
      </div>
    </div>
  );
}
