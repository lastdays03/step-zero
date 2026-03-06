"use client";

import { useRouter } from "next/navigation";
import { Search, Sparkles } from "lucide-react";
import { useAuth } from "@/providers/AuthProvider";
import { HERO_SUGGESTIONS } from "@/features/roadmap/components/roadmap-constants";
import { useAuthModal } from "../providers/AuthModalProvider";

export function ColdStartHero() {
  const { isLoggedIn } = useAuth();
  const router = useRouter();
  const { openAuthModal } = useAuthModal();

  const handleStart = () => {
    if (isLoggedIn) {
      router.push("/roadmap");
    } else {
      openAuthModal();
    }
  };

  return (
    <div className="relative flex flex-col items-center justify-center min-h-[calc(100vh-10rem)] px-6">
      {/* Grid pattern background */}
      <div
        className="absolute inset-0 opacity-40 pointer-events-none"
        style={{
          backgroundImage: "radial-gradient(circle, rgba(13,13,242,0.08) 1px, transparent 1px)",
          backgroundSize: "32px 32px",
        }}
      />

      {/* Decorative blurs */}
      <div className="absolute top-0 left-0 w-48 h-48 bg-indigo-500/5 rounded-full blur-3xl" />
      <div className="absolute bottom-0 right-0 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl" />

      <div className="relative z-10 max-w-3xl w-full text-center space-y-8">
        {/* Badge + Heading */}
        <div className="space-y-3">
          <span className="inline-block px-4 py-1.5 rounded-full bg-indigo-600/10 text-indigo-600 text-xs font-bold uppercase tracking-wider">
            Start Here
          </span>
          <h2 className="text-4xl md:text-5xl font-extrabold text-slate-900 leading-tight">
            당신의 비즈니스 여정을<br className="hidden md:block" /> 시작하세요
          </h2>
          <p className="text-slate-500 text-lg">
            아이디어를 입력하고 AI가 설계한 맞춤형 로드맵을 확인하세요.
          </p>
        </div>

        {/* CTA Button */}
        <div className="relative group">
          <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/50 to-blue-600/50 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-1000 group-hover:duration-200" />
          <button
            type="button"
            onClick={handleStart}
            className="relative w-full flex flex-col md:flex-row items-stretch gap-3 bg-white p-3 rounded-2xl shadow-xl shadow-slate-200/50 border border-slate-200 text-left cursor-pointer"
          >
            <div className="flex-1 flex items-center px-4 gap-3">
              <Search className="w-5 h-5 text-slate-400 shrink-0" />
              <span className="text-lg text-slate-400">
                예: SaaS 스타트업, 카페 프랜차이즈, 커뮤니티
              </span>
            </div>
            <div className="bg-indigo-600 hover:bg-indigo-700 text-white px-8 py-4 rounded-xl font-bold text-base transition-all flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25">
              <Sparkles className="w-5 h-5" />
              AI 로드맵 생성하기
            </div>
          </button>
        </div>

        {/* Suggested Tags */}
        <div className="flex flex-wrap justify-center gap-3">
          <span className="text-sm font-semibold text-slate-400 mr-2 self-center">추천:</span>
          {HERO_SUGGESTIONS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={handleStart}
              className="px-4 py-2 rounded-full bg-white border border-slate-200 text-slate-600 text-sm font-medium hover:border-indigo-500 hover:text-indigo-600 transition-colors"
            >
              #{tag}
            </button>
          ))}
        </div>

        {/* Feature Highlights */}
        <div className="pt-12 flex items-center justify-center gap-8">
          <div className="flex flex-col items-center gap-1">
            <span className="text-2xl">&#x1F5FA;&#xFE0F;</span>
            <span className="text-xs text-slate-500 font-medium">AI 맞춤 로드맵</span>
          </div>
          <div className="w-px h-8 bg-slate-200" />
          <div className="flex flex-col items-center gap-1">
            <span className="text-2xl">&#x2696;&#xFE0F;</span>
            <span className="text-xs text-slate-500 font-medium">법률/행정 가이드</span>
          </div>
          <div className="w-px h-8 bg-slate-200" />
          <div className="flex flex-col items-center gap-1">
            <span className="text-2xl">&#x1F465;</span>
            <span className="text-xs text-slate-500 font-medium">창업자 커뮤니티</span>
          </div>
        </div>
      </div>
    </div>
  );
}
