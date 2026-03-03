"use client";

import React from "react";
import { Bot } from "lucide-react";
import type { ChatMessage as ChatMessageType } from "../types";
import { SourcesCard } from "./SourcesCard";
import { ChatWarningBadge } from "./ChatWarningBadge";
import { renderCitationLine } from "../utils/citations";

// ------------------------------------------------------------------ //
//  ChatMessage
// ------------------------------------------------------------------ //

interface ChatMessageProps {
  message: ChatMessageType;
}

export const ChatMessage = React.memo(function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  // ---- 사용자 메시지 ----
  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-2xl rounded-tr-sm bg-blue-600 px-4 py-2.5 text-sm text-white whitespace-pre-wrap break-words">
          {message.content}
        </div>
      </div>
    );
  }

  // ---- AI 메시지 ----
  const hasSources =
    !message.isStreaming && message.sources && message.sources.length > 0;

  return (
    <div className="flex gap-2.5 items-start">
      {/* 아바타 */}
      <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-blue-500 to-purple-400 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>

      {/* 버블 */}
      <div className="max-w-[80%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700">
        {/* 콘텐츠 — 인용 배지 포함 */}
        {message.content
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line, idx) => (
            <p
              key={`line-${message.id ?? "s"}-${idx}`}
              className="mb-1.5 last:mb-0 leading-relaxed"
            >
              {renderCitationLine(line, message.sources)}
            </p>
          ))}

        {/* 스트리밍 커서 */}
        {message.isStreaming && (
          <span className="inline-block w-1.5 h-4 bg-blue-500 animate-pulse ml-0.5 -mb-0.5 rounded-sm" />
        )}

        {/* 경고 배지 */}
        {message.warning && <ChatWarningBadge warning={message.warning} />}

        {/* 출처 카드 */}
        {hasSources && <SourcesCard sources={message.sources!} />}
      </div>
    </div>
  );
});
