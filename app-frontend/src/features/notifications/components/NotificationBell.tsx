'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Bell, Heart, MessageCircle, Reply, X, CheckCheck } from 'lucide-react';
import { useNotifications } from '../hooks/useNotifications';
import { Notification } from '../api/notifications';

const ACTION_ICON: Record<string, React.ReactNode> = {
    LIKE: <Heart className="w-4 h-4 text-red-500" />,
    COMMENT: <MessageCircle className="w-4 h-4 text-blue-500" />,
    REPLY: <Reply className="w-4 h-4 text-green-500" />,
};

function timeAgo(dateStr: string): string {
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return '방금 전';
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    return `${Math.floor(hours / 24)}일 전`;
}

function NotificationItem({
    notification,
    onRead,
    onNavigate,
}: {
    notification: Notification;
    onRead: (id: number) => void;
    onNavigate: (notification: Notification) => void;
}) {
    const handleClick = () => {
        if (!notification.is_read) onRead(notification.id);
        onNavigate(notification);
    };

    return (
        <div
            onClick={handleClick}
            role="button"
            tabIndex={0}
            onKeyDown={e => e.key === 'Enter' && handleClick()}
            className={`flex items-start gap-3 px-4 py-3 border-b border-zinc-100 last:border-0 cursor-pointer transition-colors ${notification.is_read
                    ? 'bg-white hover:bg-zinc-50'
                    : 'bg-blue-50 hover:bg-blue-100/70'
                }`}
        >
            <div className="mt-0.5 flex-shrink-0">
                {ACTION_ICON[notification.action_type] ?? (
                    <Bell className="w-4 h-4 text-zinc-400" />
                )}
            </div>
            <div className="flex-1 min-w-0">
                <p className={`text-sm leading-snug ${notification.is_read ? 'text-zinc-500' : 'text-zinc-800 font-medium'}`}>
                    {notification.message}
                </p>
                <span className="text-xs text-zinc-400 mt-0.5 block">
                    {timeAgo(notification.created_at)}
                </span>
            </div>
            {!notification.is_read && (
                <span className="mt-1.5 w-2 h-2 rounded-full bg-blue-500 flex-shrink-0" />
            )}
        </div>
    );
}

export const NotificationBell = () => {
    const router = useRouter();
    const { notifications, unreadCount, markRead, markAllRead } = useNotifications();
    const [open, setOpen] = useState(false);
    const panelRef = useRef<HTMLDivElement>(null);
    const btnRef = useRef<HTMLButtonElement>(null);

    // Close on outside click
    useEffect(() => {
        const handler = (e: MouseEvent) => {
            if (
                panelRef.current &&
                !panelRef.current.contains(e.target as Node) &&
                !btnRef.current?.contains(e.target as Node)
            ) {
                setOpen(false);
            }
        };
        document.addEventListener('mousedown', handler);
        return () => document.removeEventListener('mousedown', handler);
    }, []);

    /**
     * Navigate to the growth-club page and scroll to the relevant post.
     * target_type is either "POST" or "COMMENT" — in both cases target_id
     * holds the post ID so we can build the anchor link.
     */
    const handleNavigate = (notification: Notification) => {
        if (!notification.target_id) return;
        setOpen(false);
        const anchor = `post-${notification.target_id}`;
        const url = `/growth-club#${anchor}`;
        router.push(url);

        // After navigation, wait for DOM to settle then scroll into view
        setTimeout(() => {
            const el = document.getElementById(anchor);
            if (el) {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                // Briefly highlight the card
                el.classList.add('ring-2', 'ring-blue-400', 'ring-offset-2');
                setTimeout(() => el.classList.remove('ring-2', 'ring-blue-400', 'ring-offset-2'), 2000);
            }
        }, 400);
    };

    return (
        <div className="relative">
            <button
                ref={btnRef}
                id="notification-bell-btn"
                onClick={() => setOpen(prev => !prev)}
                className="w-10 h-10 bg-white border border-slate-100 flex items-center justify-center rounded-full text-slate-400 hover:text-primary hover:border-primary/30 transition-all relative shadow-sm"
                aria-label="알림"
            >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                    <span className="absolute top-1.5 right-1.5 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-white animate-pulse" />
                )}
            </button>

            {open && (
                <div
                    ref={panelRef}
                    className="absolute right-0 top-12 w-80 max-h-[480px] bg-white border border-zinc-200 rounded-2xl shadow-2xl overflow-hidden flex flex-col z-50"
                >
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-zinc-100">
                        <h3 className="text-sm font-semibold text-zinc-800">
                            알림
                            {unreadCount > 0 && (
                                <span className="ml-2 px-1.5 py-0.5 text-xs bg-red-100 text-red-600 rounded-full">
                                    {unreadCount}
                                </span>
                            )}
                        </h3>
                        <div className="flex items-center gap-1">
                            {unreadCount > 0 && (
                                <button
                                    onClick={markAllRead}
                                    className="p-1.5 rounded-lg text-zinc-400 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                                    title="모두 읽음"
                                >
                                    <CheckCheck className="w-4 h-4" />
                                </button>
                            )}
                            <button
                                onClick={() => setOpen(false)}
                                className="p-1.5 rounded-lg text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 transition-colors"
                            >
                                <X className="w-4 h-4" />
                            </button>
                        </div>
                    </div>

                    {/* List */}
                    <div className="overflow-y-auto flex-1">
                        {notifications.length === 0 ? (
                            <div className="py-16 text-center text-zinc-400 text-sm">
                                새로운 알림이 없습니다
                            </div>
                        ) : (
                            notifications.map(n => (
                                <NotificationItem
                                    key={n.id}
                                    notification={n}
                                    onRead={markRead}
                                    onNavigate={handleNavigate}
                                />
                            ))
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};
