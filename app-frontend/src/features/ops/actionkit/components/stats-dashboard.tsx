"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Eye, TrendingUp, BarChart3, TrendingDown, Search, AlertCircle, Loader2 } from "lucide-react";
import { fetchStats } from "../api";
import type { ActionKitStatsResponse } from "../api";

interface StatsItem {
    id: number;
    name: string;
    domain?: string;
    updated_at?: string;
}

interface OpsActionKitStatsDashboardProps {
    items: StatsItem[];
}

const TIME_RANGES = [
    { key: "week", label: "최근 1주일", days: 7 },
    { key: "month", label: "최근 1개월", days: 30 },
    { key: "year", label: "올해", days: 365 },
] as const;

function DeltaBadge({ delta }: { delta: number | null }) {
    if (delta === null) {
        return (
            <span className="text-xs font-bold text-slate-400 bg-slate-100 px-2 py-1 rounded-full">
                신규
            </span>
        );
    }
    const pct = Math.round(delta * 100);
    const isUp = pct >= 0;
    return (
        <div className={`flex items-center text-sm font-bold px-2 py-1 rounded-full ${isUp ? "text-emerald-500 bg-emerald-50" : "text-rose-500 bg-rose-50"}`}>
            {isUp ? <TrendingUp className="w-3 h-3 mr-1" /> : <TrendingDown className="w-3 h-3 mr-1" />}
            {Math.abs(pct)}%
        </div>
    );
}

export function OpsActionKitStatsDashboard({ items }: OpsActionKitStatsDashboardProps) {
    const [timeRange, setTimeRange] = useState<"week" | "month" | "year">("month");
    const [stats, setStats] = useState<ActionKitStatsResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const rangeDays = TIME_RANGES.find(r => r.key === timeRange)!.days;

    const loadStats = useCallback(async (days: number) => {
        setLoading(true);
        setError(null);
        try {
            const data = await fetchStats(days);
            setStats(data);
        } catch {
            setError("통계를 불러오는 데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadStats(rangeDays);
    }, [rangeDays, loadStats]);

    // Calculate Outdated Items
    const outdatedItems = items.filter(item => {
        if (!item.updated_at) return false;
        const diffTime = Math.abs(new Date().getTime() - new Date(item.updated_at).getTime());
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return diffDays > 365;
    });

    // Item name lookup
    const getItemName = (itemId: number): string => {
        const item = items.find(i => i.id === itemId);
        return item?.name ?? `#${itemId}`;
    };

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

            {/* Header / Filter */}
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                        <BarChart3 className="w-6 h-6 text-[#36a4f2]" />
                        액션 키트 이용 통계
                    </h2>
                    <p className="text-sm text-slate-500 mt-1">유저들이 어떤 서류를 가장 많이 찾고 이용하는지 분석합니다.</p>
                </div>
                <div className="flex bg-slate-100 p-1 rounded-xl w-fit">
                    {TIME_RANGES.map(range => (
                        <button
                            key={range.key}
                            onClick={() => setTimeRange(range.key)}
                            className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${timeRange === range.key ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                        >
                            {range.label}
                        </button>
                    ))}
                </div>
            </div>

            {loading ? (
                <div className="py-20 flex justify-center items-center text-slate-400">
                    <Loader2 className="w-8 h-8 animate-spin" />
                </div>
            ) : error ? (
                <div className="py-20 text-center text-red-500">
                    <AlertCircle className="w-8 h-8 mx-auto mb-2" />
                    <p className="text-sm font-bold">{error}</p>
                </div>
            ) : !stats ? null : (
                <>
                    {/* Top Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Card className="border-none shadow-sm pb-2">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-slate-500 font-medium">총 이용 건수</CardTitle>
                            </CardHeader>
                            <CardContent className="flex items-end justify-between">
                                <div>
                                    <p className="text-3xl font-black text-slate-800">{stats.kpi.downloads.toLocaleString()}<span className="text-sm text-slate-400 font-normal ml-1">건</span></p>
                                </div>
                                <DeltaBadge delta={stats.kpi.downloads_delta} />
                            </CardContent>
                        </Card>
                        <Card className="border-none shadow-sm pb-2">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-slate-500 font-medium">총 활성 유저 (조회)</CardTitle>
                            </CardHeader>
                            <CardContent className="flex items-end justify-between">
                                <div>
                                    <p className="text-3xl font-black text-slate-800">{stats.kpi.active_users.toLocaleString()}<span className="text-sm text-slate-400 font-normal ml-1">명</span></p>
                                </div>
                                <DeltaBadge delta={stats.kpi.active_users_delta} />
                            </CardContent>
                        </Card>
                        <Card className="border-none shadow-sm pb-2">
                            <CardHeader className="pb-2">
                                <CardTitle className="text-sm text-slate-500 font-medium">인당 이용 건수</CardTitle>
                            </CardHeader>
                            <CardContent className="flex items-end justify-between">
                                <div>
                                    <p className="text-3xl font-black text-slate-800">{stats.kpi.per_user}<span className="text-sm text-slate-400 font-normal ml-1">건</span></p>
                                </div>
                                <DeltaBadge delta={stats.kpi.per_user_delta} />
                            </CardContent>
                        </Card>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Popular Docs Ranking */}
                        <Card className="lg:col-span-2 border-none shadow-sm">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <TrendingUp className="w-5 h-5 text-indigo-500" />
                                    인기 서류 TOP 5
                                </CardTitle>
                                <CardDescription>가장 많이 이용된 서류 순위입니다.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {stats.popular_items.length === 0 ? (
                                    <p className="text-sm text-slate-400 py-8 text-center">아직 충분한 데이터가 수집되지 않았습니다.</p>
                                ) : (
                                    <div className="space-y-1">
                                        {stats.popular_items.map((doc, idx) => (
                                            <div key={doc.item_id} className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100">
                                                <div className="flex items-center gap-4">
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${idx < 3 ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                                        {idx + 1}
                                                    </div>
                                                    <h4 className="font-bold text-slate-700">{getItemName(doc.item_id)}</h4>
                                                </div>
                                                <div className="flex items-center gap-6">
                                                    <div className="flex flex-col items-end">
                                                        <span className="text-xs text-slate-400">이용</span>
                                                        <span className="text-sm font-bold text-slate-700 flex items-center gap-1">
                                                            <Eye className="w-3 h-3 text-slate-400" /> {doc.count}
                                                        </span>
                                                    </div>
                                                    {doc.trend !== null && (
                                                        <div className="flex flex-col items-end">
                                                            <span className="text-xs text-slate-400">변화</span>
                                                            <span className={`text-sm font-bold flex items-center gap-1 ${doc.trend >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                                                                {doc.trend >= 0 ? <TrendingUp className="w-3 h-3" /> : <TrendingDown className="w-3 h-3" />}
                                                                {doc.trend >= 0 ? "+" : ""}{Math.round(doc.trend * 100)}%
                                                            </span>
                                                        </div>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>

                        {/* Popular Search Keywords + Insight */}
                        <Card className="border-none shadow-sm">
                            <CardHeader>
                                <CardTitle className="text-lg flex items-center gap-2">
                                    <Search className="w-5 h-5 text-emerald-500" />
                                    인기 검색어
                                </CardTitle>
                                <CardDescription>유저들이 라이브러리에서 많이 찾는 검색어입니다.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                {stats.search_keywords.length === 0 ? (
                                    <p className="text-sm text-slate-400 py-4 text-center">아직 검색 데이터가 수집되지 않았습니다.</p>
                                ) : (
                                    <div className="flex flex-wrap gap-2 mt-2">
                                        {stats.search_keywords.map((kw, i) => (
                                            <div key={kw.keyword} className="px-3 py-1.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-lg text-sm font-medium flex items-center gap-2">
                                                <span className="text-emerald-500 font-bold text-xs">{i + 1}</span>
                                                {kw.keyword}
                                                <span className="text-slate-400 text-xs">({kw.count})</span>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                {stats.insight && (
                                    <div className="mt-8 p-4 bg-orange-50 rounded-xl border border-orange-100">
                                        <h5 className="font-bold text-sm text-orange-800 flex items-center gap-2 mb-2">
                                            인사이트
                                        </h5>
                                        <p className="text-xs text-orange-700 leading-relaxed">
                                            {stats.insight}
                                        </p>
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </>
            )}
        </div>
    );
}
