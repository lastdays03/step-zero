'use client';

import React, { useState, useEffect } from 'react';
import { PostCard, CreatePostForm } from '@/features/growth-club';
import { usePosts } from '@/features/growth-club';
import { useAuth } from '@/providers/AuthProvider';
import { Search } from 'lucide-react';

export default function GrowthClubPage() {
    const { isLoggedIn } = useAuth();
    const [category, setCategory] = useState('all');

    // 검색 관련 상태
    const [searchQuery, setSearchQuery] = useState('');
    const [searchType, setSearchType] = useState('title');
    const [activeSearch, setActiveSearch] = useState({ query: '', type: 'title' });

    const { posts, isLoading, error, refetch } = usePosts(category, activeSearch.query, activeSearch.type);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setActiveSearch({ query: searchQuery, type: searchType });
    };

    // 알림에서 넘어올 때 URL 해시(#post-N)로 해당 게시글 스크롤
    useEffect(() => {
        if (isLoading) return;
        const hash = window.location.hash; // e.g. "#post-42"
        if (!hash) return;
        const el = document.getElementById(hash.slice(1));
        if (el) {
            setTimeout(() => {
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                el.classList.add('ring-2', 'ring-blue-400', 'ring-offset-2');
                setTimeout(() => el.classList.remove('ring-2', 'ring-blue-400', 'ring-offset-2'), 2000);
            }, 100);
        }
    }, [isLoading]);

    return (
        <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
            <header className="mb-10 flex flex-col sm:flex-row justify-between items-start sm:items-end gap-6">
                <div className="text-center sm:text-left">
                    <h1 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
                        그로스 클럽
                    </h1>
                    <p className="mt-2 text-zinc-500 dark:text-zinc-400">
                        창업가들과 성공 경험을 공유하고 소통하며 함께 성장하세요.
                    </p>
                </div>

                <form onSubmit={handleSearch} className="flex flex-row gap-2 w-full sm:w-auto">
                    <select
                        value={searchType}
                        onChange={(e) => setSearchType(e.target.value)}
                        className="rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-3 py-2 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none"
                    >
                        <option value="title">제목</option>
                        <option value="content">내용</option>
                    </select>
                    <div className="relative flex-1 sm:w-64">
                        <input
                            type="text"
                            placeholder="검색어를 입력하세요..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full rounded-xl border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-800 px-4 py-2 pl-10 text-sm focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none placeholder:text-zinc-400"
                        />
                        <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-400" />
                    </div>
                </form>
            </header>

            <div className="grid grid-cols-1 gap-8">
                {isLoggedIn ? (
                    <section>
                        <CreatePostForm onSuccess={refetch} />
                    </section>
                ) : null}

                <nav className="flex items-center gap-1 border-b border-zinc-200 dark:border-zinc-800">
                    {[
                        { id: 'all', label: '전체' },
                        { id: 'hot', label: '🔥 인기글' },
                        { id: 'free', label: '자유게시판' },
                        { id: 'neighborhood', label: '동네 소식' },
                        { id: 'industry', label: '업종 이야기' },
                    ].map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setCategory(tab.id)}
                            className={`px-4 py-3 text-sm font-medium transition-colors relative ${category === tab.id
                                ? 'text-blue-600 dark:text-blue-400'
                                : 'text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
                                }`}
                        >
                            {tab.label}
                            {category === tab.id && (
                                <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400" />
                            )}
                        </button>
                    ))}
                </nav>

                <main className="space-y-6">
                    {isLoading ? (
                        <div className="py-10 text-center text-zinc-500">소중한 정보를 불러오는 중입니다...</div>
                    ) : error ? (
                        <div className="py-10 text-center text-red-500">데이터를 불러오지 못했습니다.</div>
                    ) : posts?.length === 0 ? (
                        <div className="py-20 text-center bg-zinc-50 dark:bg-zinc-900/50 rounded-2xl border-2 border-dashed border-zinc-200 dark:border-zinc-800">
                            <p className="text-zinc-500">아직 소식이 없네요. 첫 번째 소식의 주인공이 되어보세요!</p>
                        </div>
                    ) : (
                        posts?.map((post) => <PostCard key={post.id} post={post} onDeleteSuccess={refetch} />)
                    )}
                </main>
            </div>
        </div>
    );
}
