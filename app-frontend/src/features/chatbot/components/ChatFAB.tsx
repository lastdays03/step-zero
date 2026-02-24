"use client";

import { Button } from "@/components/ui/button";
import { Sparkles, X } from "lucide-react";

interface ChatFABProps {
  isOpen: boolean;
  onClick: () => void;
}

export function ChatFAB({ isOpen, onClick }: ChatFABProps) {
  return (
    <div className="fixed bottom-28 md:bottom-8 right-6 md:right-8 z-50">
      <Button
        onClick={onClick}
        className="w-14 h-14 md:w-auto md:h-auto group flex items-center justify-center md:justify-start md:gap-3 bg-slate-900 hover:bg-slate-800 text-white p-0 md:pl-4 md:pr-6 md:py-4 rounded-full shadow-[0_4px_20px_rgba(54,164,242,0.4)] transition-all hover:scale-105 active:scale-95 border-none"
      >
        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0">
          {isOpen ? (
            <X className="w-4 h-4 text-white" />
          ) : (
            <Sparkles className="w-4 h-4 text-white" />
          )}
        </div>
        <span className="hidden md:block font-bold text-sm tracking-tight text-white">
          {isOpen ? "닫기" : "AI에게 물어보기"}
        </span>
      </Button>
    </div>
  );
}
