"use client";

import React from 'react';
import { DashboardData } from '../hooks/useDashboard';
import { ArrowRight, Timer, Sparkles } from 'lucide-react';

interface GrowthClubCardProps {
    onlineCount: number;
}

export const GrowthClubCard = ({ onlineCount }: GrowthClubCardProps) => {
    return (
        <div className="bg-slate-900 rounded-3xl p-6 shadow-sm text-white relative overflow-hidden group h-full flex flex-col justify-between transition-all hover:shadow-lg hover:shadow-slate-900/20">
            {/* Content Left */}
            <div className="space-y-3 z-10">
                <div className="flex items-center space-x-2">
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                    </span>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">LIVE: GROWTH CLUB</span>
                </div>
                <p className="text-base font-bold leading-snug tracking-tight text-white">
                    {onlineCount}명의 동료 창업자와<br />실시간으로 소통하기
                </p>
            </div>

            {/* Avatar Pile Right */}
            <div className="flex -space-x-3 relative z-10 mr-2">
                <div className="w-10 h-10 rounded-full border-2 border-slate-900 bg-pink-500 flex items-center justify-center text-xs font-bold text-white shadow-sm">
                    A
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-slate-900 bg-sky-400 flex items-center justify-center text-xs font-bold text-white shadow-sm">
                    B
                </div>
                <div className="w-10 h-10 rounded-full border-2 border-slate-900 bg-primary flex items-center justify-center text-[10px] font-bold text-white shadow-sm">
                    +{onlineCount}
                </div>
            </div>
        </div>
    );
};
