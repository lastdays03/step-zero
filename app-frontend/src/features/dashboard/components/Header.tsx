"use client";

import React from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { Bell, Search } from 'lucide-react';

export const Header = () => {
    const { data } = useDashboard();
    const userName = data?.user_name || 'Alex';
    const today = new Date().toLocaleDateString('ko-KR', { month: 'long', day: 'numeric', weekday: 'long' });

    return (
        <header className="h-20 flex items-center justify-between px-8 bg-background/80 backdrop-blur-md sticky top-0 z-30 border-b border-transparent">
            <div>
                <h2 className="text-xl font-bold text-slate-900">좋은 아침입니다, {userName}님.</h2>
                <p className="text-xs text-slate-500 mt-1">오늘 귀하의 비즈니스를 공식적으로 등록해 봅시다.</p>
            </div>

            <div className="flex items-center gap-4">
                <button className="w-10 h-10 bg-white border border-slate-100 flex items-center justify-center rounded-full text-slate-400 hover:text-primary hover:border-primary/30 transition-all relative shadow-sm">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white" />
                </button>
            </div>
        </header>
    );
};
