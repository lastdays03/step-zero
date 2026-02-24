"use client";

import { Bot } from "lucide-react";
import type { ChatMessage } from "../types/chat";
import { renderAnswerLine } from "../utils/renderAnswerLine";

interface ChatBubbleProps {
  message: ChatMessage;
}

export function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === "user";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[80%] rounded-xl rounded-tr-none bg-blue-600 px-4 py-2.5 text-sm text-white whitespace-pre-wrap">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2 items-start">
      <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0 mt-0.5">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="max-w-[80%] rounded-xl rounded-tl-none border border-slate-200 bg-white px-4 py-2.5 text-sm text-slate-700">
        {message.content
          .split("\n")
          .filter((line) => line.trim().length > 0)
          .map((line, idx) => (
            <p key={`msg-${message.id}-${idx}`} className="mb-1.5 last:mb-0 leading-relaxed">
              {renderAnswerLine(line, `msg-${message.id}-${idx}`)}
            </p>
          ))}
        {message.source && (
          <span className="mt-1 inline-block text-[10px] text-slate-400">
            {message.source === "legal_rag" ? "법률 RAG" : "일반 AI"}
          </span>
        )}
      </div>
    </div>
  );
}
