"use client";

import React from 'react';
import { Calendar, ChevronLeft } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { OpsAnnouncement } from '../../ops/announcements/types';

interface AnnouncementDetailViewProps {
    announcement: OpsAnnouncement;
}

export const AnnouncementDetailView: React.FC<AnnouncementDetailViewProps> = ({ announcement }) => {
    const router = useRouter();

    const publishDate = announcement.published_at ? new Date(announcement.published_at) : new Date(announcement.created_at);
    const formattedDate = new Intl.DateTimeFormat('ko-KR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
    }).format(publishDate);

    return (
        <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
            <button
                onClick={() => router.back()}
                className="mb-6 flex items-center text-zinc-500 hover:text-zinc-800 transition-colors gap-1 group"
            >
                <ChevronLeft size={20} className="group-hover:-translate-x-0.5 transition-transform" />
                <span className="text-sm font-medium">목록으로 돌아가기</span>
            </button>

            <article className="bg-white dark:bg-zinc-900 rounded-2xl shadow-sm border border-zinc-200 dark:border-zinc-800 overflow-hidden">
                <header className="p-8 border-b border-zinc-100 dark:border-zinc-800 bg-zinc-50/50 dark:bg-zinc-800/30">
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                        <span className="px-2.5 py-1 bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 text-xs font-bold rounded-lg uppercase tracking-wider">
                            Notice
                        </span>
                        <div className="flex items-center text-zinc-400 text-xs gap-1.5">
                            <Calendar size={14} />
                            <span>{formattedDate}</span>
                        </div>
                    </div>
                    <h1 className="text-3xl font-extrabold text-zinc-900 dark:text-white leading-tight">
                        {announcement.title}
                    </h1>
                </header>

                <div className="p-8">
                    <div className="prose dark:prose-invert max-w-none text-zinc-700 dark:text-zinc-300 leading-relaxed whitespace-pre-wrap">
                        {announcement.content}
                    </div>
                </div>

                <footer className="p-8 bg-zinc-50/30 dark:bg-zinc-800/20 border-t border-zinc-100 dark:border-zinc-800">
                    <p className="text-xs text-zinc-400">
                        * 본 공지사항은 관리자에 의해 작성되었습니다. 관련 문의사항은 고객센터를 이용해주세요.
                    </p>
                </footer>
            </article>
        </div>
    );
};
