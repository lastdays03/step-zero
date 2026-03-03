"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/providers/AuthProvider";
import { SocialAuthModal } from "@/features/auth/components/SocialAuthModal";
import { Sparkles } from "lucide-react";
import { useChatProvider } from "../providers/ChatProvider";

export function ChatFAB() {
  const { openPanel } = useChatProvider();
  const { isLoggedIn } = useAuth();
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const handleClick = () => {
    if (isLoggedIn) {
      openPanel();
    } else {
      setIsAuthModalOpen(true);
    }
  };

  return (
    <>
      <div className="fixed bottom-28 md:bottom-8 right-6 md:right-8 z-50">
        <Button
          onClick={handleClick}
          className="w-14 h-14 md:w-auto md:h-auto group flex items-center justify-center md:justify-start md:gap-3 bg-slate-900 hover:bg-slate-800 text-white p-0 md:pl-4 md:pr-6 md:py-3.5 rounded-full shadow-[0_4px_20px_rgba(59,130,246,0.35)] transition-all hover:scale-105 active:scale-95 border-none"
        >
          <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-500 to-purple-400 flex items-center justify-center shrink-0">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="hidden md:block font-bold text-sm tracking-tight text-white">
            StepZero AI에게 물어보기
          </span>
        </Button>
      </div>
      {!isLoggedIn && (
        <SocialAuthModal
          isOpen={isAuthModalOpen}
          onClose={() => setIsAuthModalOpen(false)}
        />
      )}
    </>
  );
}
