"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Map, Briefcase, Users, Settings, LogIn, UserCircle, Grid, FileText, CheckSquare, LogOut, Sparkles } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import { SocialAuthModal } from '@/features/auth/components/SocialAuthModal';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

export const MobileNav = () => {
    const pathname = usePathname();
    const { isLoggedIn, user, logout } = useAuth();
    const [isAuthModalOpen, setIsAuthModalOpen] = React.useState(false);

    const navItems = [
        { icon: LayoutDashboard, label: '홈', href: '/dashboard' },
        { icon: Map, label: '로드맵', href: '#' },
        { icon: Briefcase, label: '서류함', href: '#' },
        {
            icon: isLoggedIn ? UserCircle : LogIn,
            label: isLoggedIn ? (user?.full_name || user?.username || '마이') : '로그인',
            onClick: !isLoggedIn ? () => setIsAuthModalOpen(true) : undefined,
            href: undefined,
            isProfile: isLoggedIn
        },
    ];

    return (
        <>
            {/* Bottom Navigation Bar */}
            <nav className="fixed bottom-0 w-full bg-white/95 backdrop-blur-xl border-t border-slate-200/60 pb-8 pt-2 px-6 z-40 md:hidden shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
                <ul className="flex justify-around items-center">
                    {navItems.map((item) => {
                        const isActive = item.href ? pathname === item.href : false;
                        const Content = (
                            <div className={`flex flex-col items-center p-2 transition-all active:scale-90 ${isActive ? 'text-primary' : 'text-slate-400 hover:text-slate-600'}`}>
                                <item.icon className={`w-6 h-6 ${isActive ? 'fill-primary/10 stroke-[2.5px]' : 'stroke-[2px]'}`} />
                                <span className={`text-[10px] font-bold mt-1 ${isActive ? 'text-primary' : ''}`}>{item.label}</span>
                            </div>
                        );

                        if (item.isProfile) {
                            return (
                                <li key={item.label}>
                                    <DropdownMenu>
                                        <DropdownMenuTrigger asChild>
                                            <button className="w-full focus:outline-none">
                                                {Content}
                                            </button>
                                        </DropdownMenuTrigger>
                                        <DropdownMenuContent align="end" side="top" className="w-56 mb-2 rounded-2xl bg-white/95 backdrop-blur-xl border-slate-200/60 shadow-2xl animate-in slide-in-from-bottom-5 duration-200">
                                            <DropdownMenuLabel className="px-3 py-2 text-xs font-semibold text-slate-400">내 계정</DropdownMenuLabel>
                                            <DropdownMenuItem className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group">
                                                <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                                                    <Users className="w-4 h-4" />
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-semibold text-slate-700">프로필 관리</span>
                                                    <span className="text-[10px] text-slate-400">신원 및 정보 수정</span>
                                                </div>
                                            </DropdownMenuItem>
                                            <DropdownMenuItem className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group">
                                                <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform">
                                                    <Sparkles className="w-4 h-4" />
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-semibold text-slate-700">구독 플랜</span>
                                                    <span className="text-[10px] text-slate-400">프로 플랜 사용 중</span>
                                                </div>
                                            </DropdownMenuItem>
                                            <DropdownMenuSeparator className="my-2 bg-slate-100" />
                                            <DropdownMenuItem
                                                onClick={logout}
                                                className="flex items-center gap-3 p-3 rounded-xl text-red-600 hover:bg-red-50 focus:bg-red-50 focus:text-red-700 cursor-pointer transition-colors group"
                                            >
                                                <div className="w-8 h-8 rounded-lg bg-red-50 flex items-center justify-center group-hover:scale-110 transition-transform">
                                                    <LogOut className="w-4 h-4" />
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-sm font-bold">로그아웃</span>
                                                    <span className="text-[10px] text-red-400">안전하게 세션 종료</span>
                                                </div>
                                            </DropdownMenuItem>
                                        </DropdownMenuContent>
                                    </DropdownMenu>
                                </li>
                            );
                        }

                        return (
                            <li key={item.label}>
                                {item.href ? (
                                    <Link href={item.href}>{Content}</Link>
                                ) : (
                                    <button onClick={item.onClick} className="w-full focus:outline-none">
                                        {Content}
                                    </button>
                                )
                                }
                            </li>
                        );
                    })}
                </ul>
            </nav>

            <SocialAuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setIsAuthModalOpen(false)}
            />
        </>
    );
};
