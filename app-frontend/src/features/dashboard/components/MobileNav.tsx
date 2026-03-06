"use client";

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LogIn, UserCircle } from 'lucide-react';
import { useAuth } from '@/providers/AuthProvider';
import {
    DropdownMenu,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { getNavItems } from '../config/nav-config';
import { AccountMenu } from './AccountMenu';
import { useAuthModal } from '../providers/AuthModalProvider';

export const MobileNav = () => {
    const pathname = usePathname();
    const { isLoggedIn, user, logout, canAccessOps } = useAuth();
    const { openAuthModal } = useAuthModal();

    const baseItems = getNavItems(canAccessOps);

    const navItems = [
        ...baseItems.map((item) => ({
            icon: item.icon,
            label: item.mobileLabel,
            href: item.href,
        })),
        {
            icon: isLoggedIn ? UserCircle : LogIn,
            label: isLoggedIn ? (user?.full_name || user?.username || '마이') : '로그인',
            onClick: !isLoggedIn ? openAuthModal : undefined,
            href: undefined as string | undefined,
            isProfile: isLoggedIn,
        },
    ];

    return (
        <nav className="fixed bottom-0 w-full bg-white/95 backdrop-blur-xl border-t border-slate-200/60 pb-[max(2rem,env(safe-area-inset-bottom))] pt-2 px-6 z-40 md:hidden shadow-[0_-4px_20px_rgba(0,0,0,0.03)]">
            <ul className="flex justify-around items-center">
                {navItems.map((item) => {
                    const isActive = item.href ? pathname === item.href : false;
                    const Content = (
                        <div className={`flex flex-col items-center p-2 transition-all active:scale-90 ${isActive ? 'text-primary' : 'text-slate-400 hover:text-slate-600'}`}>
                            <item.icon className={`w-6 h-6 ${isActive ? 'fill-primary/10 stroke-[2.5px]' : 'stroke-[2px]'}`} />
                            <span className={`text-[10px] font-bold mt-1 ${isActive ? 'text-primary' : ''}`}>{item.label}</span>
                        </div>
                    );

                    if ('isProfile' in item && item.isProfile) {
                        return (
                            <li key={item.label}>
                                <DropdownMenu>
                                    <DropdownMenuTrigger asChild>
                                        <button className="w-full focus:outline-none">
                                            {Content}
                                        </button>
                                    </DropdownMenuTrigger>
                                    <AccountMenu variant="mobile" onLogout={logout} />
                                </DropdownMenu>
                            </li>
                        );
                    }

                    return (
                        <li key={item.label}>
                            {item.href ? (
                                <Link href={item.href} aria-label={item.label}>{Content}</Link>
                            ) : (
                                <button onClick={'onClick' in item ? item.onClick : undefined} className="w-full focus:outline-none">
                                    {Content}
                                </button>
                            )}
                        </li>
                    );
                })}
            </ul>
        </nav>
    );
};
