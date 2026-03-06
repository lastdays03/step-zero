"use client";

import React from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { NotificationBell } from '@/features/notifications/components/NotificationBell';

function getGreeting(): string {
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 12) return '좋은 아침입니다';
    if (hour >= 12 && hour < 18) return '좋은 오후입니다';
    return '좋은 저녁입니다';
}

export const Header = () => {
    const { user } = useAuth();
    const userName = user?.full_name || user?.username || '게스트';

    return (
        <header className="h-20 flex items-center justify-between px-8 bg-background/80 backdrop-blur-md sticky top-0 z-30 border-b border-transparent">
            <div>
                <h2 className="text-xl font-bold text-slate-900">{getGreeting()}, {userName}님.</h2>
                <p className="text-xs text-slate-500 mt-1">오늘도 한 걸음 더 나아가 봅시다.</p>
            </div>

            <div className="flex items-center gap-4">
                <NotificationBell />
            </div>
        </header>
    );
};
