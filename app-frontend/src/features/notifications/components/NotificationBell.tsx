"use client";

import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Bell, Heart, MessageSquare, Reply, X, ChevronDown, ChevronUp } from 'lucide-react';
import { notificationsApi } from '../api';
import { Notification } from '../types';
import { formatTimeAgo } from '@/features/growth-club/hooks/useTimeAgo';
import { useAuth } from '@/providers/AuthProvider';
import { useRouter } from 'next/navigation';

interface NotificationGroup {
    id: string;
    notifications: Notification[];
    is_read: boolean;
    created_at: string;
    type: string;
    content: string;
    link?: string;
}

type GroupedItem = Notification | NotificationGroup;

export const NotificationBell = () => {
    const { user } = useAuth();
    const router = useRouter();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [showAll, setShowAll] = useState(false);
    const [hasUnread, setHasUnread] = useState(false);
    const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
    const dropdownRef = useRef<HTMLDivElement>(null);

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
            const axiosErr = error as { response?: { status?: number } };
            if (axiosErr?.response?.status !== 401) {
                console.error('Failed to fetch notifications:', error);
            }
        }
    };

    useEffect(() => {
        const load = async () => {
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
        };
        void load();

        let interval: ReturnType<typeof setInterval> | null = null;
        if (user) {
            interval = setInterval(fetchNotifications, 60000);
        }

        return () => {
            if (interval) clearInterval(interval);
        };
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [user]);

    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
                setIsOpen(false);
                setShowAll(false);
                setExpandedGroups(new Set());
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
            setExpandedGroups(new Set());
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
                setNotifications((prev: Notification[]) => prev.map(n => n.id === notif.id ? { ...n, is_read: true } : n));
            } catch (error) {
                console.error('Failed to mark as read:', error);
            }
        }
        if (notif.link) {
            router.push(notif.link);
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

    const toggleGroup = (e: React.MouseEvent, groupId: string) => {
        e.stopPropagation();
        setExpandedGroups((prev: Set<string>) => {
            const next = new Set(prev);
            if (next.has(groupId)) next.delete(groupId);
            else next.add(groupId);
            return next;
        });
    };

    // Grouping logic
    const groupedNotifications: GroupedItem[] = useMemo(() => {
        const result: GroupedItem[] = [];
        const notices = notifications.filter(n => n.type === 'notice');
        const others = notifications.filter(n => n.type !== 'notice');

        const sortedNotices = [...notices].sort((a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );

        let currentGroup: NotificationGroup | null = null;

        sortedNotices.forEach(notif => {
            if (!currentGroup) {
                currentGroup = {
                    id: `group-${notif.id}`,
                    notifications: [notif],
                    is_read: notif.is_read,
                    created_at: notif.created_at,
                    type: 'notice',
                    content: notif.content,
                    link: notif.link
                };
            } else {
                const groupTime = new Date(currentGroup.created_at).getTime();
                const notifTime = new Date(notif.created_at).getTime();
                const diffHours = (groupTime - notifTime) / (1000 * 60 * 60);

                if (diffHours <= 1) {
                    currentGroup.notifications.push(notif);
                    if (!notif.is_read) currentGroup.is_read = false;
                } else {
                    result.push((currentGroup.notifications.length > 1 ? currentGroup : currentGroup.notifications[0]) as GroupedItem);
                    currentGroup = {
                        id: `group-${notif.id}`,
                        notifications: [notif],
                        is_read: notif.is_read,
                        created_at: notif.created_at,
                        type: 'notice',
                        content: notif.content,
                        link: notif.link
                    };
                }
            }
        });

        if (currentGroup !== null) {
            const g = currentGroup as NotificationGroup;
            result.push((g.notifications.length > 1 ? g : g.notifications[0]) as GroupedItem);
        }

        const final = [...result, ...others].sort((a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );

        return final;
    }, [notifications]);

    const displayItems = showAll ? groupedNotifications : groupedNotifications.slice(0, 5);

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
                        {groupedNotifications.length === 0 ? (
                            <div className="p-8 text-center text-zinc-400 text-sm">
                                새로운 알림이 없습니다.
                            </div>
                        ) : (
                            <>
                                {displayItems.map((item) => {
                                    const isGroup = 'notifications' in item;

                                    if (isGroup) {
                                        const group = item as NotificationGroup;
                                        const isExpanded = expandedGroups.has(group.id);
                                        const count = group.notifications.length;
                                        const content = `${group.content.split(']')[0] || '[공지]'} ${group.content.split(']')[1]?.trim() || ''} 외 ${count - 1}건`;

                                        return (
                                            <React.Fragment key={group.id}>
                                                <div
                                                    className={`group/item p-4 border-b border-zinc-50 hover:bg-zinc-50 transition-colors cursor-pointer relative ${!group.is_read ? 'bg-blue-50/30' : ''} ${isExpanded ? 'bg-zinc-50' : ''}`}
                                                    onClick={(e) => toggleGroup(e, group.id)}
                                                >
                                                    <div className="flex gap-3 pr-6">
                                                        <div className="mt-1">{getIcon(group.type)}</div>
                                                        <div className="flex-1">
                                                            <p className="text-sm font-medium text-zinc-700 leading-tight mb-1">{content}</p>
                                                            <span className="text-[10px] text-zinc-400">
                                                                {formatTimeAgo(group.created_at)}
                                                            </span>
                                                        </div>
                                                    </div>
                                                    <div className="absolute right-3 top-4 text-zinc-300 group-hover/item:text-zinc-500 transition-colors">
                                                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                                                    </div>
                                                </div>
                                                {isExpanded && group.notifications.map((notif) => (
                                                    <div
                                                        key={notif.id}
                                                        className={`group/sub-item p-4 pl-12 border-b border-zinc-50 hover:bg-zinc-100 transition-all cursor-pointer relative ${!notif.is_read ? 'bg-blue-50/20' : 'bg-zinc-50/30'}`}
                                                        onClick={() => handleNotificationClick(notif)}
                                                    >
                                                        <div className="flex-1">
                                                            <p className="text-sm text-zinc-600 leading-tight mb-1">{notif.content}</p>
                                                            <span className="text-[10px] text-zinc-400">
                                                                {formatTimeAgo(notif.created_at)}
                                                            </span>
                                                        </div>
                                                        <button
                                                            onClick={(e) => handleDelete(e, notif.id)}
                                                            className="absolute right-3 top-4 opacity-40 hover:opacity-100 p-1 hover:bg-zinc-200 rounded text-zinc-400 transition-all"
                                                        >
                                                            <X size={14} />
                                                        </button>
                                                    </div>
                                                ))}
                                            </React.Fragment>
                                        );
                                    }

                                    const notif = item as Notification;
                                    return (
                                        <div
                                            key={notif.id}
                                            className={`group/item p-4 border-b border-zinc-50 hover:bg-zinc-50 transition-colors cursor-pointer relative ${!notif.is_read ? 'bg-blue-50/30' : ''}`}
                                            onClick={() => handleNotificationClick(notif)}
                                        >
                                            <div className="flex gap-3 pr-6">
                                                <div className="mt-1">{getIcon(notif.type)}</div>
                                                <div className="flex-1">
                                                    <p className="text-sm text-zinc-700 leading-tight mb-1">{notif.content}</p>
                                                    <span className="text-[10px] text-zinc-400">
                                                        {formatTimeAgo(notif.created_at)}
                                                    </span>
                                                </div>
                                            </div>
                                            <button
                                                onClick={(e) => handleDelete(e, notif.id)}
                                                className="absolute right-3 top-4 opacity-40 group-hover/item:opacity-100 p-1 hover:bg-zinc-200 rounded text-zinc-400 transition-all"
                                            >
                                                <X size={14} />
                                            </button>
                                        </div>
                                    );
                                })}
                                {groupedNotifications.length > 5 && !showAll && (
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
