"use client";

import React from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { ProgressCard } from './ProgressCard';
import { RoadmapStepper } from './RoadmapStepper';
import { GrowthClubCard } from './GrowthClubCard';
import { Bell, Sparkles, FileText, Download, Plus, Clock, CheckSquare } from 'lucide-react';

export const DashboardView = () => {
    const { data, loading: isLoading } = useDashboard();

    if (isLoading || !data) {
        return <div className="p-8 text-center">Loading...</div>;
    }

    return (
        <div className="">
            {/* Main Grid: 4 Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

                {/* 1. Progress Card (Span 3) */}
                <div className="md:col-span-3 lg:col-span-3 h-full">
                    <ProgressCard phase={data.current_phase} />
                </div>

                {/* 2. Growth Club (Span 1) */}
                <div className="md:col-span-1 lg:col-span-1 h-full">
                    <GrowthClubCard onlineCount={data.growth_club.founders_online} />
                </div>

                {/* 3. Roadmap (Full Span 4) */}
                <div className="md:col-span-3 lg:col-span-4">
                    <RoadmapStepper steps={data.roadmap} />
                </div>

                {/* 4. Action Kit / Documents (Span 2) */}
                <div className="md:col-span-2 lg:col-span-2 bg-white/90 backdrop-blur-sm border border-white/50 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)]">
                    <h3 className="font-bold text-slate-800 mb-4 flex items-center gap-2">
                        <span className="w-1 h-5 bg-[#36a4f2] rounded-full"></span>
                        필요 서류
                    </h3>
                    <div className="space-y-3">
                        {/* Doc Item 1 */}
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-blue-200 hover:bg-white transition-all group cursor-pointer">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-red-100 text-red-500 flex items-center justify-center">
                                    <FileText className="w-4 h-4" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-slate-700 group-hover:text-[#36a4f2]">정관</p>
                                    <p className="text-xs text-slate-400">PDF • 2.4 MB</p>
                                </div>
                            </div>
                            <button className="text-slate-400 hover:text-[#36a4f2] transition-colors">
                                <Download className="w-5 h-5" />
                            </button>
                        </div>
                        {/* Doc Item 2 */}
                        <div className="flex items-center justify-between p-3 rounded-lg bg-slate-50 border border-slate-100 hover:border-blue-200 hover:bg-white transition-all group cursor-pointer">
                            <div className="flex items-center gap-3">
                                <div className="w-8 h-8 rounded bg-blue-100 text-[#36a4f2] flex items-center justify-center">
                                    <FileText className="w-4 h-4" />
                                </div>
                                <div>
                                    <p className="text-sm font-semibold text-slate-700 group-hover:text-[#36a4f2]">사업자 등록 확인서 (EIN)</p>
                                    <p className="text-xs text-slate-400">PDF • 1.1 MB</p>
                                </div>
                            </div>
                            <button className="text-slate-400 hover:text-[#36a4f2] transition-colors">
                                <Download className="w-5 h-5" />
                            </button>
                        </div>
                    </div>
                    <button className="w-full mt-4 py-2 border border-dashed border-slate-300 text-slate-500 rounded-lg text-sm font-medium hover:bg-slate-50 hover:border-[#36a4f2] hover:text-[#36a4f2] transition-colors flex items-center justify-center gap-2">
                        <Plus className="w-4 h-4" />
                        누락된 서류 업로드
                    </button>
                </div>

                {/* 5. Stat Card 1: Timer (Span 1) */}
                <div className="md:col-span-1 lg:col-span-1 bg-white/90 backdrop-blur-sm border border-white/50 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] flex flex-col justify-center items-center text-center">
                    <div className="w-12 h-12 rounded-full bg-orange-100 text-orange-500 flex items-center justify-center mb-3">
                        <Clock className="w-6 h-6" />
                    </div>
                    <h4 className="text-xl font-bold text-slate-800">3일</h4>
                    <p className="text-xs text-slate-500">세금 마감일까지 3일 남음</p>
                </div>

                {/* 6. Stat Card 2: Tasks (Span 1) */}
                <div className="md:col-span-1 lg:col-span-1 bg-white/90 backdrop-blur-sm border border-white/50 rounded-xl p-6 shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] flex flex-col justify-center items-center text-center">
                    <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-500 flex items-center justify-center mb-3">
                        <CheckSquare className="w-6 h-6" />
                    </div>
                    <h4 className="text-2xl font-bold text-slate-800">8/12</h4>
                    <p className="text-xs text-slate-500">8/12 작업 완료</p>
                </div>
            </div>

            {/* Floating FAB */}
            <div className="fixed bottom-8 right-8 z-50">
                <button className="group flex items-center gap-3 bg-slate-900 hover:bg-slate-800 text-white pl-4 pr-6 py-3 rounded-full shadow-[0_0_15px_rgba(54,164,242,0.5)] transition-all hover:scale-105 active:scale-95">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center animate-pulse">
                        <Sparkles className="w-4 h-4" />
                    </div>
                    <span className="font-semibold text-sm">법률 AI에게 물어보기</span>
                </button>
            </div>
        </div>
    );
};
