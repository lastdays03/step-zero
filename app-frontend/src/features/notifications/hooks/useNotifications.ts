'use client';

import { useState, useEffect, useCallback } from 'react';
import { notificationsApi, Notification } from '../api/notifications';
import { useAuth } from '@/providers/AuthProvider';

export const useNotifications = () => {
    const { isLoggedIn } = useAuth();
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const fetchNotifications = useCallback(async () => {
        if (!isLoggedIn) return;
        setIsLoading(true);
        try {
            const data = await notificationsApi.getNotifications();
            setNotifications(data);
        } catch {
            // Silently fail for notifications
        } finally {
            setIsLoading(false);
        }
    }, [isLoggedIn]);

    const markRead = useCallback(async (id: number) => {
        try {
            await notificationsApi.markRead(id);
            setNotifications(prev =>
                prev.map(n => n.id === id ? { ...n, is_read: true } : n)
            );
        } catch { /* ignore */ }
    }, []);

    const markAllRead = useCallback(async () => {
        try {
            await notificationsApi.markAllRead();
            setNotifications(prev => prev.map(n => ({ ...n, is_read: true })));
        } catch { /* ignore */ }
    }, []);

    // Poll every 30 seconds when logged in
    useEffect(() => {
        if (!isLoggedIn) return;
        fetchNotifications();
        const interval = setInterval(fetchNotifications, 30_000);
        return () => clearInterval(interval);
    }, [fetchNotifications, isLoggedIn]);

    const unreadCount = notifications.filter(n => !n.is_read).length;

    return {
        notifications,
        unreadCount,
        isLoading,
        fetchNotifications,
        markRead,
        markAllRead,
    };
};
