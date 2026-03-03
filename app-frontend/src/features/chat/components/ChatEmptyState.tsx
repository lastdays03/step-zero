"use client";

import { Sparkles, Lightbulb } from "lucide-react";
import { useChatProvider } from "../providers/ChatProvider";

// ------------------------------------------------------------------ //
//  추천 질문 데이터
// ------------------------------------------------------------------ //

const DEFAULT_SUGGESTIONS = [
  "사업자등록 절차 알려줘",
  "법인과 개인사업자 차이?",
  "스타트업 초기 자금 조달 방법은?",
];

function getRoadmapSuggestions(stepTitle: string | null): string[] {
  if (!stepTitle) return DEFAULT_SUGGESTIONS;
  return [
    `"${stepTitle}" 단계에서 준비할 서류가 뭐야?`,
    `현재 단계 체크리스트 보여줘`,
    `${stepTitle} 관련 법령 알려줘`,
  ];
}

// ------------------------------------------------------------------ //
//  ChatEmptyState
// ------------------------------------------------------------------ //

interface ChatEmptyStateProps {
  onSendMessage: (message: string) => void;
}

export function ChatEmptyState({ onSendMessage }: ChatEmptyStateProps) {
  const { roadmapContext, hasRoadmapContext } = useChatProvider();

  const suggestions = hasRoadmapContext
    ? getRoadmapSuggestions(roadmapContext?.stepTitle ?? null)
    : DEFAULT_SUGGESTIONS;

  return (
    <div className="flex flex-col items-center justify-center h-full px-6 py-8">
      {/* 로고 */}
      <div className="w-12 h-12 rounded-full bg-gradient-to-tr from-blue-500 to-purple-400 flex items-center justify-center mb-4">
        <Sparkles className="w-6 h-6 text-white" />
      </div>

      <h2 className="text-lg font-semibold text-slate-800 mb-1">
        StepZero AI
      </h2>
      <p className="text-sm text-slate-500 mb-6 text-center">
        창업에 필요한 모든 것을 물어보세요
      </p>

      {/* 로드맵 컨텍스트 표시 */}
      {hasRoadmapContext && roadmapContext?.stepTitle && (
        <p className="text-xs text-blue-600 bg-blue-50 rounded-full px-3 py-1 mb-4">
          현재 단계: {roadmapContext.stepTitle}
        </p>
      )}

      {/* 추천 질문 */}
      <div className="w-full max-w-sm space-y-2">
        <div className="flex items-center gap-1.5 mb-2">
          <Lightbulb className="w-3.5 h-3.5 text-amber-500" />
          <span className="text-xs font-medium text-slate-500">추천 질문</span>
        </div>

        {suggestions.map((question) => (
          <button
            key={question}
            type="button"
            onClick={() => onSendMessage(question)}
            className="w-full text-left px-4 py-2.5 rounded-xl border border-slate-200 bg-white text-sm text-slate-700 hover:border-blue-300 hover:bg-blue-50 transition-colors"
          >
            &ldquo;{question}&rdquo;
          </button>
        ))}
      </div>
    </div>
  );
}
