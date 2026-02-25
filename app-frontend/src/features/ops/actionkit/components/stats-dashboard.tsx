"use client";

import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Download, Bookmark, TrendingUp, Users, Calendar, BarChart3, TrendingDown, Search } from "lucide-react";

const POPULAR_DOCS = [
    { title: "근로계약서 (정규직)", downloads: 1250, saves: 430, trend: "+12%" },
    { title: "상가임대차계약서", downloads: 890, saves: 310, trend: "+5%" },
    { title: "주주간계약서", downloads: 650, saves: 490, trend: "+24%" },
    { title: "비밀유지계약서 (NDA)", downloads: 580, saves: 210, trend: "-2%" },
    { title: "취업규칙 샘플", downloads: 420, saves: 180, trend: "+8%" },
];

const SEARCH_KEYWORDS = ["근로계약서", "스톡옵션", "동업계약", "투자계약", "개인정보", "사직서"];

export function OpsActionKitStatsDashboard() {
    const [timeRange, setTimeRange] = useState<"week" | "month" | "year">("month");

    return (
        <div className="space-y-6 animate-in fade-in duration-500">
            {/* Header / Filter */}
            <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
                <div>
                    <h2 className="text-xl font-bold text-slate-800 flex items-center gap-2">
                        <BarChart3 className="w-6 h-6 text-[#36a4f2]" />
                        액션 키트 이용 통계
                    </h2>
                    <p className="text-sm text-slate-500 mt-1">유저들이 어떤 서류를 가장 많이 찾고 다운로드하는지 분석합니다.</p>
                </div>
                <div className="flex bg-slate-100 p-1 rounded-xl w-fit">
                    {(["week", "month", "year"] as const).map(range => (
                        <button
                            key={range}
                            onClick={() => setTimeRange(range)}
                            className={`px-4 py-1.5 text-xs font-bold rounded-lg transition-all ${timeRange === range ? "bg-white text-slate-800 shadow-sm" : "text-slate-500 hover:text-slate-700"}`}
                        >
                            {range === "week" ? "최근 1주일" : range === "month" ? "최근 1개월" : "올해"}
                        </button>
                    ))}
                </div>
            </div>

            {/* Top Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-none shadow-sm pb-2">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-500 font-medium">총 다운로드 수</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-end justify-between">
                        <div>
                            <p className="text-3xl font-black text-slate-800">4,520<span className="text-sm text-slate-400 font-normal ml-1">건</span></p>
                        </div>
                        <div className="flex items-center text-emerald-500 text-sm font-bold bg-emerald-50 px-2 py-1 rounded-full">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            15%
                        </div>
                    </CardContent>
                </Card>
                <Card className="border-none shadow-sm pb-2">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-500 font-medium">총 활성 유저 (조회)</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-end justify-between">
                        <div>
                            <p className="text-3xl font-black text-slate-800">1,284<span className="text-sm text-slate-400 font-normal ml-1">명</span></p>
                        </div>
                        <div className="flex items-center text-emerald-500 text-sm font-bold bg-emerald-50 px-2 py-1 rounded-full">
                            <TrendingUp className="w-3 h-3 mr-1" />
                            8%
                        </div>
                    </CardContent>
                </Card>
                <Card className="border-none shadow-sm pb-2">
                    <CardHeader className="pb-2">
                        <CardTitle className="text-sm text-slate-500 font-medium">스타터 팩 다운로드율</CardTitle>
                    </CardHeader>
                    <CardContent className="flex items-end justify-between">
                        <div>
                            <p className="text-3xl font-black text-slate-800">42<span className="text-sm text-slate-400 font-normal ml-1">%</span></p>
                        </div>
                        <div className="flex items-center text-rose-500 text-sm font-bold bg-rose-50 px-2 py-1 rounded-full">
                            <TrendingDown className="w-3 h-3 mr-1" />
                            3%
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Popular Docs Ranking */}
                <Card className="lg:col-span-2 border-none shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <TrendingUp className="w-5 h-5 text-indigo-500" />
                            인기 다운로드 서류 TOP 5
                        </CardTitle>
                        <CardDescription>가장 많이 다운로드되고 찜(서랍장) 된 서류 순위입니다.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="space-y-1">
                            {POPULAR_DOCS.map((doc, idx) => (
                                <div key={idx} className="flex items-center justify-between p-3 rounded-xl hover:bg-slate-50 transition-colors border border-transparent hover:border-slate-100">
                                    <div className="flex items-center gap-4">
                                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm ${idx < 3 ? 'bg-indigo-100 text-indigo-600' : 'bg-slate-100 text-slate-500'}`}>
                                            {idx + 1}
                                        </div>
                                        <h4 className="font-bold text-slate-700">{doc.title}</h4>
                                    </div>
                                    <div className="flex items-center gap-6">
                                        <div className="flex flex-col items-end">
                                            <span className="text-xs text-slate-400">다운로드</span>
                                            <span className="text-sm font-bold text-slate-700 flex items-center gap-1">
                                                <Download className="w-3 h-3 text-slate-400" /> {doc.downloads}
                                            </span>
                                        </div>
                                        <div className="flex flex-col items-end">
                                            <span className="text-xs text-slate-400">서랍장 찜</span>
                                            <span className="text-sm font-bold text-slate-700 flex items-center gap-1">
                                                <Bookmark className="w-3 h-3 text-yellow-500 fill-yellow-500" /> {doc.saves}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </CardContent>
                </Card>

                {/* Popular Search Keywords */}
                <Card className="border-none shadow-sm">
                    <CardHeader>
                        <CardTitle className="text-lg flex items-center gap-2">
                            <Search className="w-5 h-5 text-emerald-500" />
                            실시간 검색어
                        </CardTitle>
                        <CardDescription>유저들이 라이브러리에서 많이 찾는 검색어입니다.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="flex flex-wrap gap-2 mt-2">
                            {SEARCH_KEYWORDS.map((kw, i) => (
                                <div key={i} className="px-3 py-1.5 bg-slate-50 text-slate-600 border border-slate-200 rounded-lg text-sm font-medium flex items-center gap-2">
                                    <span className="text-emerald-500 font-bold text-xs">{i + 1}</span>
                                    {kw}
                                </div>
                            ))}
                        </div>
                        <div className="mt-8 p-4 bg-orange-50 rounded-xl border border-orange-100">
                            <h5 className="font-bold text-sm text-orange-800 flex items-center gap-2 mb-2">
                                💡 인사이트
                            </h5>
                            <p className="text-xs text-orange-700 leading-relaxed">
                                최근 <span className="font-bold border-b border-orange-300">"주주간계약서"</span> 및 <span className="font-bold border-b border-orange-300">"투자계약"</span> 검색량이 저번달 대비 <strong>24% 급증</strong>했습니다. 관련 스타터 팩을 상단에 고정하는 것을 권장합니다.
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
