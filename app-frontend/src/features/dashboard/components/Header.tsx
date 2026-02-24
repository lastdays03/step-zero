"use client";

import React from 'react';
import { useAuth } from '@/providers/AuthProvider';
import { NotificationBell } from '@/features/notifications';

export const Header = () => {
    const { user } = useAuth();
    const userName = user?.full_name || user?.username || '게스트';

    return (
        <header className="h-20 flex items-center justify-between px-8 bg-background/80 backdrop-blur-md sticky top-0 z-30 border-b border-transparent">
            <div>
                <h2 className="text-xl font-bold text-slate-900">좋은 아침입니다, {userName}님.</h2>
                <p className="text-xs text-slate-500 mt-1">오늘 귀하의 비즈니스를 공식적으로 등록해 봅시다.</p>
            </div>

            <div className="flex items-center gap-4">
                <NotificationBell />
            </div>
        </header>
    );
};
