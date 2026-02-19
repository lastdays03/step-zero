"use client";

import React from 'react';
import { DashboardData } from '../hooks/useDashboard';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Check, Lock } from 'lucide-react';

interface RoadmapStepperProps {
    steps: DashboardData['roadmap'];
}

export const RoadmapStepper = ({ steps }: RoadmapStepperProps) => {
    const normalizedSteps = steps.map((step) => ({
        ...step,
        status: String(step.status || "").toLowerCase(),
    }));

    return (
        <Card className="bg-white/90 backdrop-blur-sm rounded-3xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] border border-white/50 relative overflow-hidden group">
            <CardContent className="p-8">
                <div className="flex justify-between items-center mb-8">
                    <h3 className="font-bold text-lg text-slate-800">나의 로드맵</h3>
                    <button
                        type="button"
                        onClick={() => {
                            window.location.href = "/roadmap";
                        }}
                        className="text-sm text-[#36a4f2] font-medium hover:underline flex items-center"
                    >
                        전체 계획 보기
                    </button>
                </div>

                <div className="relative">
                    {/* Horizontal Scroll Container */}
                    <div className="overflow-x-auto pb-4 -mx-4 px-4 hide-scrollbar scroll-smooth">
                        <div className="flex items-start md:items-center space-x-8 min-w-max relative">

                            {/* Timeline Line - Positioned absolute relative to the scrollable content width */}
                            <div className="absolute top-[24px] left-6 right-6 h-[2.5px] bg-slate-100 z-0" />

                            {normalizedSteps.map((step, index) => (
                                <div key={index} className={`flex flex-col items-start md:items-center text-left md:text-center relative z-10 w-[120px] flex-shrink-0 group transition-all duration-500 ${step.status === 'locked' ? 'opacity-50' : 'opacity-100'}`}>
                                    <div className="relative mb-3 w-full flex justify-start md:justify-center">
                                        {step.status === 'current' && (
                                            <span className="absolute inline-flex h-12 w-12 rounded-full bg-[#36a4f2] opacity-25 animate-ping"></span>
                                        )}
                                        <div className={`w-12 h-12 rounded-full flex items-center justify-center border-4 border-white shadow-xl relative z-10 transition-transform hover:scale-110 ${step.status === 'completed' ? 'bg-green-500 shadow-green-100' :
                                            step.status === 'current' ? 'bg-[#36a4f2] shadow-blue-200' :
                                                'bg-slate-200 shadow-none'
                                            }`}>
                                            {step.status === 'completed' ? (
                                                <Check className="w-5 h-5 text-white" />
                                            ) : step.status === 'current' ? (
                                                <span className="font-bold text-sm text-white">{index + 1}</span>
                                            ) : (
                                                <Lock className="w-5 h-5 text-slate-400" />
                                            )}
                                        </div>
                                    </div>

                                    <div className="w-full px-1">
                                        <h4 className={`font-bold text-sm truncate ${step.status === 'current' ? 'text-[#36a4f2]' : 'text-slate-900'}`}>{step.title}</h4>
                                        <div className="mt-1">
                                            {step.status === 'current' ? (
                                                <Badge className="bg-blue-50 text-blue-600 border-none font-bold text-[9px] hover:bg-blue-100 px-2 py-0">
                                                    현재 작업
                                                </Badge>
                                            ) : (
                                                <p className="text-[10px] font-medium truncate text-slate-400">
                                                    {step.status === 'completed' ? (step.date || '완료됨') : '잠금 해제 대기'}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Fade effect on the right to indicate more content */}
                <div className="absolute top-0 right-0 bottom-0 w-12 bg-gradient-to-l from-white/90 to-transparent pointer-events-none md:hidden" />
            </CardContent>
        </Card>
    );
};
