"use client";

import React from 'react';
import { DashboardData } from '../hooks/useDashboard';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Timer, ArrowRight } from 'lucide-react';

interface ProgressCardProps {
    phase: DashboardData['current_phase'];
    daysLeft: number;
    nextTitle: string | null;
    endowedProgress?: number | null;
    readinessLabel?: string | null;
}

export const ProgressCard = ({ phase, daysLeft, nextTitle, endowedProgress, readinessLabel }: ProgressCardProps) => {
    const displayProgress = endowedProgress ?? phase.progress;
    return (
        <Card className="bg-white rounded-3xl shadow-sm border border-slate-100 relative overflow-hidden group h-full transition-all hover:shadow-md">
            <div className="absolute -right-6 -top-6 w-32 h-32 bg-primary/5 rounded-full blur-3xl transition-all duration-500 group-hover:bg-primary/10"></div>
            <CardContent className="p-8">
                <div className="flex justify-between items-start mb-8 relative z-10">
                    <div className="space-y-1">
                        <Badge variant="secondary" className="bg-primary/10 text-primary text-[10px] font-black tracking-wider uppercase mb-2 hover:bg-primary/20 border-none px-3 py-1">
                            현재 진행 단계
                        </Badge>
                        <h2 className="text-2xl font-bold text-slate-900 tracking-tight leading-tight">
                            {phase.title}
                        </h2>
                    </div>

                    <div className="relative w-24 h-24 flex items-center justify-center">
                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                            <circle
                                cx="50"
                                cy="50"
                                r="45"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="8"
                                className="text-slate-100"
                            />
                            <circle
                                cx="50"
                                cy="50"
                                r="45"
                                fill="none"
                                stroke="currentColor"
                                strokeWidth="8"
                                strokeDasharray={`${displayProgress * 2.827}, 282.7`}
                                strokeLinecap="round"
                                className="text-primary drop-shadow-[0_0_8px_rgba(37,123,244,0.3)] transition-all duration-1000 ease-out"
                            />
                        </svg>
                        <div className="absolute flex flex-col items-center">
                            <span className="text-xl font-black text-slate-900 leading-none">
                                {displayProgress}%
                            </span>
                            <span className="text-[9px] font-bold text-slate-400 mt-1 uppercase tracking-tighter">
                                {endowedProgress != null ? "준비 단계 포함" : "완료"}
                            </span>
                        </div>
                    </div>
                </div>

                {readinessLabel && (
                    <div className="relative z-10 mb-4">
                        <span className="inline-flex items-center rounded-full bg-[#36a4f2]/10 px-3 py-1 text-xs font-semibold text-[#36a4f2]">
                            {readinessLabel}
                        </span>
                    </div>
                )}

                <div className="flex items-center space-x-3 text-sm text-slate-500 font-medium relative z-10 mb-8">
                    <div className="flex items-center space-x-1.5">
                        <Timer className="w-4 h-4 text-primary" />
                        <span>D-{Math.max(daysLeft, 0)}</span>
                    </div>
                    <div className="w-1 h-1 bg-slate-300 rounded-full"></div>
                    <span>다음: {nextTitle || "다음 단계를 확인하세요"}</span>
                </div>

                <Button
                    onClick={() => {
                        window.location.href = "/roadmap";
                    }}
                    className="w-full bg-slate-900 text-white py-6 rounded-2xl font-bold text-sm flex items-center justify-center hover:bg-slate-800 transition-all shadow-lg shadow-slate-200 active:scale-[0.98] group/btn"
                >
                    <span>신청 계속하기</span>
                    <ArrowRight className="w-4 h-4 ml-2 transition-transform group-hover/btn:translate-x-1" />
                </Button>
            </CardContent>
        </Card>
    );
};
