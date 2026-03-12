"use client";

import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Send, Loader2 } from "lucide-react";

const MAX_LENGTH = 2000;

interface ChatInputProps {
  onSend: (content: string) => void;
  isStreaming: boolean;
}

export function ChatInput({ onSend, isStreaming }: ChatInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // 자동 높이 조절
  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 120)}px`;
  }, [value]);

  const canSend = value.trim().length > 0 && !isStreaming;

  const handleSend = () => {
    if (!canSend) return;
    onSend(value.trim());
    setValue("");
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const remaining = MAX_LENGTH - value.length;

  return (
    <div data-testid="chat-input" className="border-t border-slate-200 px-3 py-2 bg-white rounded-b-2xl">
      <div className="flex items-end gap-2">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value.slice(0, MAX_LENGTH))}
          onKeyDown={handleKeyDown}
          data-testid="chat-input-field"
          placeholder="메시지를 입력하세요..."
          rows={1}
          disabled={isStreaming}
          className="flex-1 resize-none rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400 focus:ring-1 focus:ring-blue-400/30 disabled:opacity-50 max-h-[120px] bg-slate-50"
        />
        <Button
          onClick={handleSend}
          disabled={!canSend}
          data-testid="chat-input-submit"
          size="icon"
          className="h-9 w-9 shrink-0 rounded-lg bg-blue-600 hover:bg-blue-700 disabled:opacity-50"
        >
          {isStreaming ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
        </Button>
      </div>
      {remaining <= 200 && (
        <p
          className={`text-right text-[10px] mt-1 ${remaining <= 50 ? "text-red-500" : "text-slate-400"}`}
        >
          {remaining}자 남음
        </p>
      )}
    </div>
  );
}
