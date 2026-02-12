"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Map, Briefcase, Users, Settings, Sparkles } from 'lucide-react';

export const MobileNav = () => {
    const pathname = usePathname();

    const navItems = [
        { icon: LayoutDashboard, label: '대시보드', href: '/dashboard' },
        { icon: Map, label: '로드맵', href: '#' },
        { icon: Briefcase, label: '액션 키트', href: '#' },
        { icon: Users, label: '그로스', href: '#' },
        { icon: Settings, label: '설정', href: '#' },
    ];

    return (
        <>
            {/* Floating AI Button */}
            <button className="fixed bottom-24 right-5 bg-primary hover:bg-primary/90 text-white rounded-full px-5 py-3 shadow-lg shadow-primary/30 flex items-center space-x-2 transition-all transform hover:scale-105 z-40 md:hidden group">
                <Sparkles className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                <span className="font-bold text-sm">법률 AI에게 질문하기</span>
            </button>

            {/* Bottom Navigation Bar */}
            <nav className="fixed bottom-0 w-full bg-white/80 backdrop-blur-xl border-t border-slate-200/50 pb-8 pt-2 px-6 z-40 md:hidden">
                <ul className="flex justify-between items-center">
                    {navItems.map((item) => {
                        const isActive = pathname === item.href;
                        return (
                            <li key={item.label}>
                                <Link
                                    href={item.href}
                                    className={`flex flex-col items-center p-2 transition-colors ${isActive ? 'text-primary' : 'text-slate-400 hover:text-slate-600'
                                        }`}
                                >
                                    <item.icon className={`w-6 h-6 ${isActive ? 'fill-primary/10' : ''}`} />
                                    <span className="text-[10px] font-bold mt-1">{item.label}</span>
                                </Link>
                            </li>
                        );
                    })}
                </ul>
            </nav>
        </>
    );
};
