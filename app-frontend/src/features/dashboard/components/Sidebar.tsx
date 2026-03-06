"use client";

import React from 'react';
import Link from 'next/link';
import { LogOut, Sparkles, ChevronRight } from 'lucide-react';
import { usePathname } from 'next/navigation';

import { useAuth } from '@/providers/AuthProvider';
import { SocialAuthModal } from '@/features/auth/components/SocialAuthModal';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getNavItems } from '../config/nav-config';
import { Users } from 'lucide-react';

export const Sidebar = () => {
    const pathname = usePathname();
    const { isLoggedIn, user, logout, canAccessOps } = useAuth();
    const [isAuthModalOpen, setIsAuthModalOpen] = React.useState(false);

    const menuItems = getNavItems(canAccessOps);

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
                        const isActive = pathname === item.href || pathname.startsWith(`${item.href}/`);
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
                                    <item.icon className={`w-5 h-5 shrink-0 ${isActive ? 'text-primary' : 'text-slate-400 group-hover:text-slate-600'}`} />
                                    <div className="flex flex-col">
                                        <span className="text-sm">{item.label}</span>
                                        <span className={`text-[10px] leading-tight ${isActive ? 'text-primary/60' : 'text-slate-400'}`}>{item.caption}</span>
                                    </div>
                                </div>
                                {item.badge && !isActive && (
                                    <Badge className="text-[10px] px-2 py-0.5 rounded-md font-bold bg-blue-100 text-blue-600 border-none hover:bg-blue-100 uppercase">
                                        {item.badge}
                                    </Badge>
                                )}
                            </Link>
                        );
                    })}
                </nav>

                <div className="p-4 mt-auto">
                    {isLoggedIn ? (
                        <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                                <button
                                    type="button"
                                    className="w-full bg-white rounded-2xl p-4 flex items-center justify-between group cursor-pointer hover:bg-slate-50 transition-all border border-slate-100 shadow-sm text-left"
                                >
                                    <div className="flex items-center gap-3">
                                        <div className="relative">
                                            <Avatar className="w-10 h-10 border-2 border-white shadow-sm">
                                                <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || 'Guest'}`} />
                                                <AvatarFallback className="bg-primary/10 text-primary">{user?.username?.[0] || 'U'}</AvatarFallback>
                                            </Avatar>
                                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-500 border-2 border-white rounded-full"></div>
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-sm font-bold text-slate-900 leading-none">{user?.username || '사용자'}</span>
                                            <span className="text-[10px] text-slate-500 mt-1">프로 플랜</span>
                                        </div>
                                    </div>
                                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-450 group-hover:translate-x-0.5 transition-all" />
                                </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-64 p-2 rounded-2xl bg-white/95 backdrop-blur-xl border-slate-200/60 shadow-2xl animate-in fade-in zoom-in duration-200">
                                <DropdownMenuLabel className="px-3 py-2 text-xs font-semibold text-slate-400">내 계정</DropdownMenuLabel>
                                <DropdownMenuItem asChild className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group">
                                    <Link href="/profile">
                                        <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center text-blue-600 group-hover:scale-110 transition-transform">
                                            <Users className="w-4 h-4" />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-sm font-semibold text-slate-700">프로필 관리</span>
                                            <span className="text-[10px] text-slate-400">신원 및 정보 수정</span>
                                        </div>
                                    </Link>
                                </DropdownMenuItem>
                                <DropdownMenuItem asChild className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group">
                                    <Link href="/billing">
                                        <div className="w-8 h-8 rounded-lg bg-orange-50 flex items-center justify-center text-orange-600 group-hover:scale-110 transition-transform">
                                            <Sparkles className="w-4 h-4" />
                                        </div>
                                        <div className="flex flex-col">
                                            <span className="text-sm font-semibold text-slate-700">구독 플랜</span>
                                            <span className="text-[10px] text-slate-400">프로 플랜 사용 중</span>
                                        </div>
                                    </Link>
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
                    ) : (
                        <Button
                            onClick={() => setIsAuthModalOpen(true)}
                            className="w-full h-auto bg-slate-900 hover:bg-slate-800 text-white rounded-2xl p-4 flex items-center justify-between group transition-all shadow-lg shadow-slate-200 border-none"
                        >
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 rounded-full bg-white/10 flex items-center justify-center">
                                    <Sparkles className="w-5 h-5 text-blue-400" />
                                </div>
                                <div className="flex flex-col items-start">
                                    <span className="text-sm font-bold text-white leading-none">로그인하기</span>
                                    <span className="text-[10px] text-slate-400 mt-1">로드맵 소장하기</span>
                                </div>
                            </div>
                            <ChevronRight className="w-4 h-4 text-slate-500 group-hover:text-white group-hover:translate-x-1 transition-all" />
                        </Button>
                    )}
                </div>
            </aside>

            <SocialAuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setIsAuthModalOpen(false)}
            />
        </>
    );
};
