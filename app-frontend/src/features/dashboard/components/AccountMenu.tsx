"use client";

import Link from 'next/link';
import { LogOut, Sparkles, Users } from 'lucide-react';
import {
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
} from "@/components/ui/dropdown-menu";

interface AccountMenuProps {
    variant: "desktop" | "mobile";
    onLogout: () => void;
}

export function AccountMenu({ variant, onLogout }: AccountMenuProps) {
    const isDesktop = variant === "desktop";

    return (
        <DropdownMenuContent
            align="end"
            {...(!isDesktop && { side: "top" })}
            className={`${isDesktop ? "w-64" : "w-56 mb-2"} p-2 rounded-2xl bg-white/95 backdrop-blur-xl border-slate-200/60 shadow-2xl ${isDesktop ? "animate-in fade-in zoom-in duration-200" : "animate-in slide-in-from-bottom-5 duration-200"}`}
        >
            <DropdownMenuLabel className="px-3 py-2 text-xs font-semibold text-slate-400">
                내 계정
            </DropdownMenuLabel>
            <DropdownMenuItem
                asChild
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group"
            >
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
            <DropdownMenuItem
                asChild
                className="flex items-center gap-3 p-3 rounded-xl hover:bg-slate-50 cursor-pointer transition-colors group"
            >
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
                onClick={onLogout}
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
    );
}
