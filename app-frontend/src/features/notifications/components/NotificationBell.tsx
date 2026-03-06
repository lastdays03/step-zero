"use client";

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Bell, Heart, MessageSquare, Reply, X, ChevronDown } from 'lucide-react';
import { notificationsApi } from '../api';
import { Notification } from '../types';
import { formatTimeAgo } from '@/features/growth-club/hooks/useTimeAgo';
import { useAuth } from '@/providers/AuthProvider';
import { useRouter } from 'next/navigation';
import { useNotificationSSE } from '../hooks/useNotificationSSE';

export const NotificationBell = () => {
    const { user } = useAuth();
    const router = useRouter();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [showAll, setShowAll] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const fetchNotifications = useCallback(async () => {
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
            const axiosErr = error as { response?: { status?: number } };
            if (axiosErr?.response?.status !== 401) {
                console.error('Failed to fetch notifications:', error);
            }
        }
    }, [user]);

    useEffect(() => {
        const timeoutId = window.setTimeout(() => {
            void fetchNotifications();
        }, 0);

        return () => window.clearTimeout(timeoutId);
    }, [fetchNotifications]);

    // SSE: re-fetch when new notification arrives
    useNotificationSSE({
        enabled: !!user,
        onMessage: fetchNotifications,
    });

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
                setShowAll(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleToggle = () => {
        if (!user) return;
        setIsOpen(!isOpen);
        if (!isOpen) {
            setShowAll(false);
        }
    };

    const handleReadAll = async () => {
        try {
            await notificationsApi.readAllNotifications();
            setHasUnread(false);
            setNotifications((prev: Notification[]) => prev.map(n => ({ ...n, is_read: true })));
        } catch (error) {
            console.error('Failed to mark all as read:', error);
        }
    };

    const handleNotificationClick = async (notif: Notification) => {
        if (!notif.is_read) {
            try {
                await notificationsApi.markAsRead(notif.id);
                setNotifications((prev: Notification[]) => {
                    const updated = prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n);
                    setHasUnread(updated.some(n => !n.is_read));
                    return updated;
                });
            } catch (error) {
                console.error('Failed to mark as read:', error);
            }
        }
        if (notif.link) {
            // /growth-club/123 → /growth-club#post-123 (legacy link migration)
            const resolved = notif.link.replace(/^\/growth-club\/(\d+)$/, '/growth-club#post-$1');
            router.push(resolved);
            setIsOpen(false);
        }
    };

    const handleDelete = async (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        try {
            await notificationsApi.deleteNotification(id);
            setNotifications((prev: Notification[]) => prev.filter(n => n.id !== id));
        } catch (error) {
            console.error('Failed to delete notification:', error);
        }
    };

    const sortedNotifications = [...notifications].sort((a, b) =>
        new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    );

    const displayItems = showAll ? sortedNotifications : sortedNotifications.slice(0, 5);

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
                aria-label="알림"
                className="w-10 h-10 bg-white border border-zinc-100 flex items-center justify-center rounded-full text-zinc-400 hover:text-primary hover:border-primary/30 transition-all relative shadow-sm"
            >
                <Bell className="w-5 h-5" />
                <span className="sr-only">알림</span>
                {hasUnread && (
                    <span className="absolute top-2.5 right-2.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-pulse" />
                )}
            </button>

            {isOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white border border-zinc-100 rounded-xl shadow-xl z-50 overflow-hidden">
                    <div className="p-4 border-b border-zinc-50 flex justify-between items-center bg-zinc-50/50">
                        <span className="font-bold text-zinc-800">알림</span>
                        <div className="flex items-center gap-2">
                            {hasUnread && (
                                <button
                                    onClick={handleReadAll}
                                    className="text-[10px] bg-zinc-200 hover:bg-zinc-300 text-zinc-600 px-2 py-0.5 rounded transition-colors"
                                >
                                    모두 읽음
                                </button>
                            )}
                            <span className="text-xs text-zinc-500">{notifications.length}</span>
                        </div>
                    </div>
                    <div className="max-h-[32rem] overflow-y-auto">
                        {sortedNotifications.length === 0 ? (
                            <div className="p-8 text-center text-zinc-400 text-sm">
                                새로운 알림이 없습니다.
                            </div>
                        ) : (
                            <>
                                {displayItems.map((notif) => (
                                    <div
                                        key={notif.id}
                                        className={`group/item p-4 border-b border-zinc-50 hover:bg-zinc-50 transition-colors cursor-pointer relative ${!notif.is_read ? 'bg-blue-50/50 border-l-[3px] border-l-blue-500' : ''}`}
                                        onClick={() => handleNotificationClick(notif)}
                                    >
                                        <div className="flex gap-3 pr-6">
                                            <div className="mt-1">{getIcon(notif.type)}</div>
                                            <div className="flex-1">
                                                <p className={`text-sm leading-tight mb-1 ${!notif.is_read ? 'text-zinc-900 font-semibold' : 'text-zinc-600'}`}>{notif.content}</p>
                                                <span className="text-[10px] text-zinc-400">
                                                    {!notif.is_read && <span className="text-blue-500 font-bold mr-1">NEW</span>}
                                                    {formatTimeAgo(notif.created_at)}
                                                </span>
                                            </div>
                                        </div>
                                        <button
                                            onClick={(e) => handleDelete(e, notif.id)}
                                            className="absolute right-3 top-4 opacity-40 group-hover/item:opacity-100 p-1 hover:bg-zinc-200 rounded text-zinc-400 transition-all"
                                        >
                                            <X size={14} /><span className="sr-only">삭제</span>
                                        </button>
                                    </div>
                                ))}
                                {sortedNotifications.length > 5 && !showAll && (
                                    <button
                                        onClick={() => setShowAll(true)}
                                        className="w-full p-3 text-center text-xs text-zinc-500 hover:bg-zinc-50 border-t border-zinc-50 transition-colors flex items-center justify-center gap-1"
                                    >
                                        이전 알림 더보기 <ChevronDown size={12} />
                                    </button>
                                )}
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
