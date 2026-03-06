"use client";

import React from 'react';
import Link from 'next/link';
import { Sparkles, ChevronRight } from 'lucide-react';
import { usePathname } from 'next/navigation';

import { useAuth } from '@/providers/AuthProvider';
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
    DropdownMenu,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getNavItems } from '../config/nav-config';
import { AccountMenu } from './AccountMenu';
import { useAuthModal } from '../providers/AuthModalProvider';

export const Sidebar = () => {
    const pathname = usePathname();
    const { isLoggedIn, user, logout, canAccessOps } = useAuth();
    const { openAuthModal } = useAuthModal();

    const menuItems = getNavItems(canAccessOps);

    return (
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
                        <AccountMenu variant="desktop" onLogout={logout} />
                    </DropdownMenu>
                ) : (
                    <Button
                        onClick={openAuthModal}
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
    );
};
