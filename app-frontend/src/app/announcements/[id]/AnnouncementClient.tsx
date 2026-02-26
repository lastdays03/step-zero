"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, CalendarClock } from 'lucide-react';
import { announcementsApi, Announcement } from '@/features/announcements/api';

export default function AnnouncementClient({ idParam }: { idParam: string }) {
    const router = useRouter();
    const [announcement, setAnnouncement] = useState<Announcement | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');

    useEffect(() => {
        const fetchAnnouncement = async () => {
            try {
                if (!idParam) return;
                const id = parseInt(idParam, 10);
                if (isNaN(id)) throw new Error('Invalid ID');
                const data = await announcementsApi.getAnnouncement(id);
                setAnnouncement(data);
            } catch (err: any) {
                setError('공지사항을 불러오는 중 오류가 발생했습니다.');
            } finally {
                setLoading(false);
            }
        };
        fetchAnnouncement();
    }, [idParam]);

    const handleBack = () => {
        router.back();
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-slate-50 flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
            </div>
        );
    }

    if (error || !announcement) {
        return (
            <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
                <p className="text-slate-500 mb-4">{error || '공지사항을 찾을 수 없습니다.'}</p>
                <button
                    onClick={handleBack}
                    className="px-4 py-2 bg-slate-800 text-white rounded-lg font-medium hover:bg-slate-700 transition"
                >
                    돌아가기
                </button>
            </div>
        );
    }

    const formattedDate = announcement.published_at
        ? new Date(announcement.published_at).toLocaleDateString('ko-KR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        })
        : '';

    return (
        <div className="min-h-screen bg-slate-50">
            <div className="max-w-3xl mx-auto px-4 py-8">
                {/* Header Actions */}
                <button
                    onClick={handleBack}
                    className="flex items-center text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors mb-8 group"
                >
                    <ChevronLeft className="w-4 h-4 mr-1 group-hover:-translate-x-1 transition-transform" />
                    목록으로
                </button>

                {/* Announcement Content */}
                <article className="bg-white rounded-2xl shadow-sm border border-slate-200 overflow-hidden">
                    <header className="px-8 py-6 border-b border-slate-100">
                        <h1 className="text-2xl font-bold text-slate-900 mb-4 leading-tight">
                            {announcement.title}
                        </h1>
                        <div className="flex items-center text-sm text-slate-500 gap-2">
                            <CalendarClock className="w-4 h-4" />
                            <span>{formattedDate}</span>
                        </div>
                    </header>

                    <div className="p-8 prose prose-slate max-w-none">
                        <div
                            className="text-slate-700 leading-relaxed whitespace-pre-wrap"
                            dangerouslySetInnerHTML={{ __html: announcement.content }}
                        />
                    </div>
                </article>
            </div>
        </div>
    );
}
