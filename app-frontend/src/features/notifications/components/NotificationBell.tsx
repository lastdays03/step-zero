"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Bell, Heart, MessageSquare, Reply } from 'lucide-react';
import { notificationsApi } from '../api';
import { Notification } from '../types';
import { formatTimeAgo } from '@/features/growth-club/hooks/useTimeAgo';
import { useAuth } from '@/providers/AuthProvider';
import { useRouter } from 'next/navigation';

export const NotificationBell = () => {
    const { user } = useAuth();
    const router = useRouter();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        const fetchNotifications = async () => {
            if (!user) {
                setNotifications([]);
                setHasUnread(false);
                return;
            }

            try {
                const data = await notificationsApi.getNotifications();
                setNotifications(data);
                setHasUnread(data.some(n => !n.is_read));
            } catch (error: unknown) {
                const err = error as { response?: { status?: number } };
                if (err.response?.status !== 401) {
                    console.error('Failed to fetch notifications:', error);
                }
            }
        };

        fetchNotifications();

        let interval: NodeJS.Timeout | null = null;
        if (user) {
            interval = setInterval(fetchNotifications, 60000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
    }, [user]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleToggle = async () => {
        if (!user) return;

        if (!isOpen && hasUnread) {
            try {
                await notificationsApi.readAllNotifications();
                setHasUnread(false);
                setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
            } catch (error: unknown) {
                const err = error as { response?: { status?: number } };
                if (err.response?.status !== 401) {
                    console.error('Failed to mark notifications as read:', error);
                }
            }
        }
        setIsOpen(!isOpen);
    };

    const handleNotificationClick = (link: string | undefined) => {
        if (link) {
            router.push(link);
            setIsOpen(false);
        }
    };

    const getIcon = (type: string) => {
        switch (type) {
            case 'like': return <Heart className="w-4 h-4 text-red-500" />;
            case 'comment': return <MessageSquare className="w-4 h-4 text-blue-500" />;
            case 'reply': return <Reply className="w-4 h-4 text-green-500" />;
            default: return <Bell className="w-4 h-4 text-zinc-400" />;
        }
    };

    if (!user) return null;

    return (
        <div className="relative" ref={dropdownRef}>
            <button
                onClick={handleToggle}
                className="w-10 h-10 bg-white border border-zinc-100 flex items-center justify-center rounded-full text-zinc-400 hover:text-primary hover:border-primary/30 transition-all relative shadow-sm"
            >
                <Bell className="w-5 h-5" />
                {hasUnread && (
                    <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-pulse" />
                )}
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-zinc-100 rounded-xl shadow-xl z-50 overflow-hidden">
                    <div className="p-4 border-b border-zinc-50 flex justify-between items-center bg-zinc-50/50">
                        <span className="font-bold text-zinc-800">알림</span>
                        <span className="text-xs text-zinc-500">{notifications.length}개의 알림</span>
                    </div>
                    <div className="max-h-96 overflow-y-auto">
                        {notifications.length === 0 ? (
                            <div className="p-8 text-center text-zinc-400 text-sm">
                                새로운 알림이 없습니다.
                            </div>
                        ) : (
                            notifications.map((n) => (
                                <div
                                    key={n.id}
                                    className={`p-4 border-b border-zinc-50 hover:bg-zinc-50 transition-colors cursor-pointer ${!n.is_read ? 'bg-blue-50/30' : ''}`}
                                    onClick={() => handleNotificationClick(n.link)}
                                >
                                    <div className="flex gap-3">
                                        <div className="mt-1">{getIcon(n.type)}</div>
                                        <div className="flex-1">
                                            <p className="text-sm text-zinc-700 leading-tight mb-1">{n.content}</p>
                                            <span className="text-[10px] text-zinc-400">
                                                {formatTimeAgo(n.created_at)}
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
