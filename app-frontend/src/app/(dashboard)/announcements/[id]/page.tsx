"use client";

import React, { useEffect, useState } from 'react';
import { toast } from "sonner";
import { useParams } from 'next/navigation';
import { AnnouncementDetailView, announcementsApi } from '@/features/announcements';
import type { OpsAnnouncement } from '@/features/ops';

export default function AnnouncementDetailPage() {
    const params = useParams();
    const id = Number(params.id);
    const [announcement, setAnnouncement] = useState<OpsAnnouncement | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;

        const loadAnnouncement = async () => {
            setIsLoading(true);
            try {
                const data = await announcementsApi.fetchPublishedAnnouncement(id);
                setAnnouncement(data);
                setError(null);
            } catch (err: unknown) {
                console.error('Failed to load announcement:', err);
                const axiosErr = err as { response?: { status?: number } };
                if (axiosErr.response?.status === 404) {
                    setError('게시가 종료된 공지입니다.');
                } else {
                    setError('공지사항을 불러오는 데 실패했습니다.');
                }
            } finally {
                setIsLoading(false);
            }
        };

        void loadAnnouncement();
    }, [id]);

    useEffect(() => {
        if (error === '게시가 종료된 공지입니다.') {
            const timer = setTimeout(() => {
                toast.warning('게시가 종료된 공지입니다.');
                window.location.href = '/dashboard';
            }, 100);
            return () => clearTimeout(timer);
        }
    }, [error]);

    if (isLoading) {
        return (
            <div className="max-w-4xl mx-auto py-20 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
                <p className="text-zinc-500">소중한 소식을 불러오는 중입니다...</p>
            </div>
        );
    }

    if (error || !announcement) {
        return (
            <div className="max-w-4xl mx-auto py-20 text-center">
                <div className="bg-red-50 dark:bg-red-900/20 p-8 rounded-2xl border border-red-100 dark:border-red-900/30">
                    <p className="text-red-600 dark:text-red-400 font-medium">{error || '존재하지 않는 공지사항입니다.'}</p>
                </div>
            </div>
        );
    }

    return <AnnouncementDetailView announcement={announcement} />;
}
