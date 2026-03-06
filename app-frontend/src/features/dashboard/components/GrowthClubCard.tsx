"use client";

import React from 'react';
import Link from 'next/link';
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface RecentPost {
    id: number;
    title: string;
    author_name: string;
    created_at: string;
    comment_count: number;
}

interface GrowthClubCardProps {
    onlineCount: number;
    recentPosts?: RecentPost[];
}

function timeAgo(dateStr: string): string {
    if (!dateStr) return "";
    const diff = Date.now() - new Date(dateStr).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return "방금";
    if (mins < 60) return `${mins}분 전`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}시간 전`;
    const days = Math.floor(hours / 24);
    return `${days}일 전`;
}

export const GrowthClubCard = ({ onlineCount, recentPosts }: GrowthClubCardProps) => {
    const posts = recentPosts?.slice(0, 2) ?? [];

    return (
        <Card className="bg-slate-900 rounded-3xl shadow-sm text-white relative overflow-hidden group h-full transition-all hover:shadow-lg hover:shadow-slate-900/20 border-none">
            <CardContent className="p-6 h-full flex flex-col justify-between">
                {/* Header */}
                <div className="space-y-3 z-10">
                    <div className="flex items-center space-x-2">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                        </span>
                        <Badge variant="outline" className="text-[10px] font-bold text-slate-400 uppercase tracking-widest border-slate-700/50 hover:bg-transparent">
                            LIVE: GROWTH CLUB
                        </Badge>
                    </div>
                    <p className="text-base font-bold leading-snug tracking-tight text-white">
                        활성 창업자 {onlineCount}명
                    </p>
                </div>

                {/* Recent Posts Preview */}
                <div className="mt-3 space-y-2 z-10">
                    {posts.length > 0 ? (
                        posts.map((post) => (
                            <div key={post.id} className="rounded-lg bg-white/10 px-3 py-2">
                                <p className="text-xs font-medium text-white line-clamp-1">{post.title}</p>
                                <p className="text-[10px] text-slate-400 mt-0.5">
                                    {post.author_name} &middot; {timeAgo(post.created_at)}
                                    {post.comment_count > 0 && ` \u00B7 댓글 ${post.comment_count}`}
                                </p>
                            </div>
                        ))
                    ) : (
                        <p className="text-xs text-slate-500">아직 게시글이 없습니다.</p>
                    )}
                    <Link
                        href="/growth-club"
                        className="inline-block text-[11px] font-semibold text-slate-400 hover:text-white transition-colors"
                    >
                        더 보기 &rarr;
                    </Link>
                </div>
            </CardContent>
        </Card>
    );
};
