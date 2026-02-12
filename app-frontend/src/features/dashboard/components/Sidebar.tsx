"use client";

import React from 'react';
import Link from 'next/link';
import { LayoutDashboard, Map, Briefcase, Users, Settings, LogOut, Sparkles, ChevronRight } from 'lucide-react';
import { usePathname } from 'next/navigation';

export const Sidebar = () => {
    const pathname = usePathname();

    const menuItems = [
        { icon: LayoutDashboard, label: '대시보드', href: '/dashboard' },
        { icon: Map, label: '나의 로드맵', href: '#' },
        { icon: Briefcase, label: '액션 키트', href: '#' },
        { icon: Users, label: '그로스 클럽', href: '#', badge: 'New' },
        { icon: Settings, label: '설정', href: '#' },
    ];

    return (
        <>
            {/* Desktop Sidebar */}
            <aside className="hidden md:flex w-72 bg-white border-r border-border min-h-screen flex-col sticky top-0">
                <div className="p-8">
                    <Link href="/dashboard" className="flex items-center gap-2">
                        <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center text-white font-bold text-xl">
                            S
                        </div>
                        <span className="text-2xl font-bold text-foreground">StepZero</span>
                    </Link>
                </div>

                <nav className="flex-1 px-4 py-8 space-y-2">
                    {menuItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <Link
                                key={item.label}
                                href={item.href}
                                className={`flex items-center justify-between px-4 py-3 rounded-xl transition-all duration-200 group ${isActive
                                    ? 'bg-secondary text-primary font-bold'
                                    : 'text-slate-500 hover:bg-slate-50 hover:text-slate-900'
                                    }`}
                            >
                                <div className="flex items-center gap-3">
                                    <item.icon className={`w-5 h-5 ${isActive ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'}`} />
                                    <span className="text-sm">{item.label}</span>
                                </div>
                                {item.badge && !isActive && (
                                    <span className="text-[10px] px-2 py-0.5 rounded-md font-bold bg-blue-100 text-blue-600 uppercase">
                                        {item.badge}
                                    </span>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 mt-auto">
                    <div className="bg-slate-50 rounded-2xl p-4 flex items-center justify-between group cursor-pointer hover:bg-slate-100 transition-all border border-slate-100">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-white shadow-sm">
                                <img src="https://api.dicebear.com/7.x/avataaars/svg?seed=Alex" alt="User" className="w-full h-full object-cover" />
                            </div>
                            <div className="flex flex-col">
                                <span className="text-sm font-bold text-slate-900 leading-none">창업자 Alex</span>
                                <span className="text-[10px] text-slate-500 mt-1">프로 플랜</span>
                            </div>
                        </div>
                        <LogOut className="w-4 h-4 text-slate-400 group-hover:text-slate-600" />
                    </div>
                </div>
            </aside>
        </>
    );
};
