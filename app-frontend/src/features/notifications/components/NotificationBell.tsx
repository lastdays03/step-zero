"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Bell, Heart, MessageSquare, Reply, ChevronDown, ChevronUp } from 'lucide-react';
import { notificationsApi } from '../api';
import { Notification } from '../types';
import { formatTimeAgo } from '@/features/growth-club/hooks/useTimeAgo';
import { useAuth } from '@/providers/AuthProvider';
import { useRouter } from 'next/navigation';

interface GroupedNotification {
    id: number;
    type: string;
    link?: string;
    content: string;
    created_at: string;
    is_read: boolean;
    items: Notification[];
}

const groupNotifications = (notifs: Notification[]): GroupedNotification[] => {
    const groups: GroupedNotification[] = [];
    const oneHour = 60 * 60 * 1000;

    notifs.forEach(notif => {
        const notifTime = new Date(notif.created_at).getTime();
        const existingGroup = groups.find(g =>
            g.type === notif.type &&
            g.link === notif.link &&
            g.items.some(item => Math.abs(new Date(item.created_at).getTime() - notifTime) <= oneHour)
        );

        if (existingGroup) {
            existingGroup.items.push(notif);
            if (notifTime > new Date(existingGroup.created_at).getTime()) {
                existingGroup.created_at = notif.created_at;
                // Inherit unread status if the newer one is unread
                if (!notif.is_read) existingGroup.is_read = false;
            }
        } else {
            groups.push({
                id: notif.id,
                type: notif.type,
                link: notif.link,
                content: notif.content, // Group summary text should ideally be derived, using the first initially
                created_at: notif.created_at,
                is_read: notif.is_read,
                items: [notif]
            });
        }
    });

    return groups.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
};

export const NotificationBell = () => {
    const { user } = useAuth();
    const router = useRouter();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);
    const [expandedGroups, setExpandedGroups] = useState<Record<number, boolean>>({});
    const [showAll, setShowAll] = useState(false);

    const toggleGroup = (e: React.MouseEvent, id: number) => {
        e.stopPropagation();
        setExpandedGroups(prev => ({ ...prev, [id]: !prev[id] }));
    };

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
            case 'announcement': return <Bell className="w-4 h-4 text-primary" />;
            default: return <Bell className="w-4 h-4 text-zinc-400" />;
        }
    };

    if (!user) return null;

    const groupedNotifications = groupNotifications(notifications);
    const displayedGroups = showAll ? groupedNotifications : groupedNotifications.slice(0, 5);

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
                            displayedGroups.map((group) => (
                                <div key={group.id} className="border-b border-zinc-50 last:border-0">
                                    <div
                                        className={`p-4 hover:bg-zinc-50 transition-colors cursor-pointer flex gap-3 ${!group.is_read ? 'bg-blue-50/30' : ''}`}
                                        onClick={() => handleNotificationClick(group.link)}
                                    >
                                        <div className="mt-1">{getIcon(group.type)}</div>
                                        <div className="flex-1">
                                            <p className="text-sm text-zinc-700 leading-tight mb-1">
                                                {group.items.length > 1 ? (
                                                    <span className="font-semibold text-blue-600">[{group.items.length}개] </span>
                                                ) : null}
                                                {group.content}
                                            </p>
                                            <div className="flex items-center justify-between mt-1">
                                                <span className="text-[10px] text-zinc-400">
                                                    {formatTimeAgo(group.created_at)}
                                                </span>
                                                {group.items.length > 1 && (
                                                    <button
                                                        onClick={(e) => toggleGroup(e, group.id)}
                                                        className="flex items-center text-[10px] text-zinc-500 hover:text-zinc-700 bg-white border border-zinc-200 px-1.5 py-0.5 rounded shadow-sm focus:outline-none"
                                                    >
                                                        {expandedGroups[group.id] ? '접기' : '더보기'}
                                                        {expandedGroups[group.id] ? <ChevronUp size={12} className="ml-0.5" /> : <ChevronDown size={12} className="ml-0.5" />}
                                                    </button>
                                                )}
                                            </div>
                                        </div>
                                    </div>
                                    {group.items.length > 1 && expandedGroups[group.id] && (
                                        <div className="bg-zinc-50/80 border-t border-zinc-100 py-1">
                                            {group.items.map((item) => (
                                                <div
                                                    key={item.id}
                                                    className="px-5 py-2.5 flex items-start gap-3 hover:bg-zinc-100 transition-colors cursor-pointer"
                                                    onClick={() => handleNotificationClick(item.link)}
                                                >
                                                    <div className="mt-0.5 opacity-50 scale-75">{getIcon(item.type)}</div>
                                                    <div className="flex-1">
                                                        <p className="text-xs text-zinc-600 leading-tight">{item.content}</p>
                                                        <span className="text-[9px] text-zinc-400 mt-1 block">
                                                            {formatTimeAgo(item.created_at)}
                                                        </span>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    )}
                                </div>
                            ))
                        )}
                        {!showAll && groupedNotifications.length > 5 && (
                            <div className="p-3 border-t border-zinc-100 bg-zinc-50/30 sticky bottom-0">
                                <button
                                    onClick={() => setShowAll(true)}
                                    className="w-full text-center text-xs font-semibold text-zinc-500 hover:text-zinc-800 transition-colors py-2 bg-white rounded-lg border border-zinc-200 shadow-sm"
                                >
                                    더 보기 ({groupedNotifications.length - 5}개)
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
