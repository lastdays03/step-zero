"use client";

import { Search, Sparkles } from "lucide-react";

interface RoadmapEmptyHeroProps {
    title?: string;
    subtitle?: string;
    onPrimaryClick: () => void;
    primaryLabel?: string;
    onRefreshClick?: () => void;
}

const SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 의류 쇼핑몰", "샐러드 배달 전문점"];

export const RoadmapEmptyHero = ({
    title = "StepZero와 함께 당신의 비즈니스 여정을 시작하세요",
    subtitle = "어떤 비즈니스를 구상 중이신가요? 업종을 입력하면 맞춤형 로드맵을 즉시 생성해 드립니다.",
    onPrimaryClick,
    primaryLabel = "AI 로드맵 생성하기",
    onRefreshClick,
}: RoadmapEmptyHeroProps) => {
    return (
        <section className="relative overflow-hidden rounded-3xl border border-slate-200 bg-slate-50/60 px-4 py-10 sm:px-6 sm:py-14">
            <div className="pointer-events-none absolute inset-0 bg-[linear-gradient(to_right,rgba(37,99,235,0.07)_1px,transparent_1px),linear-gradient(to_bottom,rgba(37,99,235,0.07)_1px,transparent_1px)] bg-[size:36px_36px]" />
            <div className="pointer-events-none absolute -left-16 -top-16 h-64 w-64 rounded-full bg-blue-300/30 blur-3xl" />
            <div className="pointer-events-none absolute -bottom-20 -right-20 h-72 w-72 rounded-full bg-indigo-300/30 blur-3xl" />

            <div className="relative mx-auto flex w-full max-w-4xl flex-col items-center text-center">
                <span className="inline-flex items-center gap-1 rounded-full border border-blue-200 bg-blue-100/60 px-3 py-1 text-xs font-semibold text-blue-700">
                    <Sparkles className="h-3 w-3" />
                    AI 기반 비즈니스 빌더
                </span>

                <h1 className="mt-5 text-3xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-5xl">
                    {title}
                </h1>
                <p className="mt-4 max-w-2xl text-sm text-slate-600 sm:text-lg">{subtitle}</p>

                <div className="mt-8 w-full max-w-3xl rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
                    <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
                        <div className="flex h-14 flex-1 items-center rounded-xl px-3">
                            <Search className="mr-2 h-5 w-5 text-slate-400" />
                            <input
                                readOnly
                                value="예: SaaS 스타트업, 카페 프랜차이즈, 커머스 등..."
                                className="w-full border-none bg-transparent text-sm text-slate-500 outline-none"
                            />
                        </div>
                        <button
                            type="button"
                            onClick={onPrimaryClick}
                            className="inline-flex h-14 items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 text-sm font-semibold text-white transition hover:bg-blue-500"
                        >
                            <Sparkles className="h-4 w-4" />
                            {primaryLabel}
                        </button>
                    </div>
                </div>

                <div className="mt-6 flex flex-wrap items-center justify-center gap-2">
                    <span className="text-xs font-semibold text-slate-500">추천 검색어:</span>
                    {SUGGESTIONS.map((keyword) => (
                        <span
                            key={keyword}
                            className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600"
                        >
                            {keyword}
                        </span>
                    ))}
                </div>

                {onRefreshClick ? (
                    <button
                        type="button"
                        onClick={onRefreshClick}
                        className="mt-6 text-xs font-semibold text-slate-500 underline decoration-slate-300 underline-offset-2 hover:text-slate-700"
                    >
                        상태 다시 확인
                    </button>
                ) : null}
            </div>
        </section>
    );
};
