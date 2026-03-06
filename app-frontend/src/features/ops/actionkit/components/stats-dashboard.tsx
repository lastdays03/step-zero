"use client";

import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, Package, Paperclip, EyeOff, Scale, Highlighter, AlertCircle } from "lucide-react";

interface StatsItem {
    id: number;
    name: string;
    domain?: string;
    updated_at?: string;
}

interface ActionKitSummary {
    total_items: number;
    items_with_files: number;
    inactive_items: number;
    total_related_laws: number;
    total_highlights: number;
}

interface OpsActionKitStatsDashboardProps {
    items: StatsItem[];
    summary: ActionKitSummary | null;
}

export function OpsActionKitStatsDashboard({ items, summary }: OpsActionKitStatsDashboardProps) {
    const outdatedItems = items.filter(item => {
        if (!item.updated_at) return false;
        const diffTime = Math.abs(new Date().getTime() - new Date(item.updated_at).getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays > 365;
    });

    const statsCards = summary
        ? [
            { icon: Package, label: "전체 항목", value: summary.total_items, color: "text-[#36a4f2]" },
            { icon: Paperclip, label: "파일 첨부", value: summary.items_with_files, color: "text-emerald-500" },
            { icon: EyeOff, label: "미공개", value: summary.inactive_items, color: "text-orange-500" },
            { icon: Scale, label: "관련 법령", value: summary.total_related_laws, color: "text-violet-500" },
            { icon: Highlighter, label: "하이라이트", value: summary.total_highlights, color: "text-amber-500" },
        ]
        : [];

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {outdatedItems.length > 0 && (
                <div className="bg-red-50 border border-red-200 rounded-2xl p-4 md:p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 shadow-sm animate-in zoom-in-95 duration-300">
                    <div className="flex items-start gap-3">
                        <div className="bg-white p-2 rounded-full shadow-sm text-red-500 shrink-0 mt-1 md:mt-0">
                            <AlertCircle className="w-6 h-6" />
                        </div>
                        <div>
                            <h3 className="font-bold text-red-800 text-lg">긴급 갱신 필요: {outdatedItems.length}건의 노후 서류가 발견되었습니다!</h3>
                            <p className="text-sm text-red-600/90 mt-1">업데이트 된 지 1년 이상 경과된 파일입니다. 최신 법령에 맞게 문서 파일을 새로 교체해주세요.</p>
                            <ul className="mt-2 space-y-1">
                                {outdatedItems.slice(0, 3).map(item => (
                                    <li key={item.id} className="text-xs font-medium text-red-700 flex items-center gap-1.5 before:content-[''] before:w-1 before:h-1 before:bg-red-400 before:rounded-full">
                                        [{item.domain === 'laws' ? '법령' : '키트'}] {item.name} <span className="text-red-400 font-normal ml-1">({new Date(item.updated_at!).toLocaleDateString()})</span>
                                    </li>
                                ))}
                                {outdatedItems.length > 3 && (
                                    <li className="text-xs font-medium text-red-500 italic pl-3">+ {outdatedItems.length - 3}건 더 보기...</li>
                                )}
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            <div>
                <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                    <BarChart3 className="w-6 h-6 text-[#36a4f2]" />
                    액션 키트 현황
                </h2>
                <p className="text-sm text-slate-500 mt-1">액션 키트 콘텐츠 현황을 한눈에 확인합니다.</p>
            </div>

            {summary ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                    {statsCards.map(({ icon: Icon, label, value, color }) => (
                        <Card key={label} className="border-none shadow-sm pb-2">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-slate-500 font-medium flex items-center gap-1.5">
                                    <Icon className={`w-4 h-4 ${color}`} />
                                    {label}
                                </CardTitle>
                            </CardHeader>
                            <CardContent>
                                <p className="text-3xl font-black text-slate-800">{value.toLocaleString()}</p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            ) : (
                <Card className="border-none shadow-sm">
                    <CardContent className="py-8 text-center text-slate-400">
                        데이터를 불러오는 중...
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
