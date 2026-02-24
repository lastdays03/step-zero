"use client";

import Link from "next/link";
import { BookOpen, Gavel } from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { computeDeadlineDate, formatDeadlineDate } from "./roadmap-utils";
import type { RoadmapDetailStep } from "./roadmap-utils";

interface RoadmapSidebarProps {
    createdAt: string;
    steps: RoadmapDetailStep[];
    overallProgress: number;
    completedSteps: number;
    totalSteps: number;
}

export function RoadmapSidebar({
    createdAt,
    steps,
    overallProgress,
    completedSteps,
    totalSteps,
}: RoadmapSidebarProps) {
    const incompleteSteps = steps.filter((s) => s.status !== "COMPLETED");
    const deadlines = incompleteSteps.slice(0, 3).map((step) => {
        const deadline = computeDeadlineDate(createdAt, steps, step);
        const formatted = formatDeadlineDate(deadline);
        return { step, ...formatted };
    });

    return (
        <div className="space-y-6">
            {/* Overall Progress Card */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-2">
                    <span className="text-sm font-medium text-slate-600">
                        전체 진행률
                    </span>
                    <span className="text-lg font-bold text-[#36a4f2]">
                        {overallProgress}%
                    </span>
                </div>
                <Progress
                    value={overallProgress}
                    className="h-2.5 bg-slate-100"
                    indicatorClassName="bg-[#36a4f2]"
                />
                <p className="mt-2 text-xs text-slate-400">
                    {completedSteps}/{totalSteps} 단계 완료
                </p>
            </div>

            {/* Upcoming Deadlines */}
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
                <div className="flex justify-between items-center mb-4">
                    <h3 className="text-lg font-bold text-slate-900">주요 일정</h3>
                </div>
                {deadlines.length > 0 ? (
                    <ul className="space-y-4">
                        {deadlines.map(({ step, month, day, daysLeft }) => (
                            <li key={step.id} className="flex gap-4 items-start">
                                <div className="flex-shrink-0 w-12 text-center bg-slate-50 rounded-lg py-1 border border-slate-100">
                                    <span className="block text-xs text-slate-400 uppercase font-semibold">
                                        {month}
                                    </span>
                                    <span className="block text-lg font-bold text-slate-800">
                                        {day}
                                    </span>
                                </div>
                                <div className="min-w-0">
                                    <h4 className="text-sm font-semibold text-slate-800 truncate">
                                        {step.title}
                                    </h4>
                                    <p className="text-xs text-slate-500 mt-0.5">
                                        {daysLeft > 0
                                            ? `${daysLeft}일 남음`
                                            : daysLeft === 0
                                              ? "오늘 마감"
                                              : `${Math.abs(daysLeft)}일 초과`}
                                    </p>
                                </div>
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p className="text-sm text-slate-500">모든 일정이 완료되었습니다.</p>
                )}
            </div>

            {/* Guidebook Card → ActionKit 창업 법령 가이드 */}
            <Link
                href="/actionkit"
                className="block bg-white rounded-2xl border border-slate-200 p-6 shadow-sm hover:shadow-md hover:border-[#36a4f2]/30 transition-all group"
            >
                <div className="flex items-start gap-4">
                    <div className="p-2.5 bg-[#36a4f2]/10 rounded-xl text-[#36a4f2] flex-shrink-0">
                        <Gavel className="w-5 h-5" />
                    </div>
                    <div className="min-w-0">
                        <h3 className="font-bold text-slate-900 mb-1">창업 법령 가이드</h3>
                        <p className="text-sm text-slate-500">
                            사업 인허가부터 법적 요건까지, 필수 법령 정보
                        </p>
                        <span className="inline-flex items-center gap-1 mt-3 text-xs font-semibold text-[#36a4f2] group-hover:underline">
                            <BookOpen className="w-3.5 h-3.5" />
                            지금 읽기
                        </span>
                    </div>
                </div>
            </Link>
        </div>
    );
}
