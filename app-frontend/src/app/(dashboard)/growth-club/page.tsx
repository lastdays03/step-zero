'use client';

import React, { Suspense, useState, useEffect } from 'react';
import { PostCard, CreatePostForm } from '@/features/growth-club';
import { usePosts } from '@/features/growth-club';
import { useAuth } from '@/providers/AuthProvider';
import { Search, X } from 'lucide-react';
import { useSearchParams } from 'next/navigation';

export default function GrowthClubPage() {
    return (
        <Suspense fallback={<div className="max-w-4xl mx-auto py-8 px-4 sm:px-6 text-center text-zinc-500">로딩 중...</div>}>
            <GrowthClubContent />
        </Suspense>
    );
}

function GrowthClubContent() {
    const { isLoggedIn } = useAuth();
    const searchParams = useSearchParams();
    const targetPostId = searchParams.get('post_id');
    const targetCommentId = searchParams.get('comment_id');

    const [category, setCategory] = useState('all');
    const [searchInput, setSearchInput] = useState('');
    const [search, setSearch] = useState('');
    const [searchType, setSearchType] = useState('all');
    const { posts, isLoading, error, refetch } = usePosts(category, search, searchType);

    // 알림을 통해 들어온 경우 해당 게시글로 스크롤
    useEffect(() => {
        if (!isLoading && targetPostId) {
            // 게시글 데이터가 로드된 후 약간의 지연을 두어 DOM 렌더링을 기다림
            const timer = setTimeout(() => {
                const element = document.getElementById(`post-${targetPostId}`);
                if (element) {
                    element.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [isLoading, targetPostId]);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        setSearch(searchInput);
    };

    const clearSearch = () => {
        setSearchInput('');
        setSearch('');
    };

    return (
        <div className="max-w-4xl mx-auto py-8 px-4 sm:px-6">
            <header className="mb-10 text-center sm:text-left">
                <h1 className="text-3xl font-extrabold text-zinc-900 dark:text-white tracking-tight">
                    그로스 클럽
                </h1>
                <p className="mt-2 text-zinc-500 dark:text-zinc-400">
                    창업가들과 성공 경험을 공유하고 소통하며 함께 성장하세요.
                </p>
            </header>

            <div className="grid grid-cols-1 gap-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1 max-w-sm ml-auto relative group">
                        <form onSubmit={handleSearch} className="relative flex items-center">
                            <div className="absolute left-3 p-1.5 pointer-events-none">
                                <Search size={18} className="text-zinc-400 group-focus-within:text-blue-500 transition-colors" />
                            </div>
                            <div className="flex w-full items-center bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all shadow-sm">
                                <select
                                    value={searchType}
                                    onChange={(e) => setSearchType(e.target.value)}
                                    className="pl-10 pr-2 py-2.5 text-xs font-semibold bg-zinc-50 dark:bg-zinc-800/50 border-r border-zinc-200 dark:border-zinc-800 focus:outline-none text-zinc-600 dark:text-zinc-400 cursor-pointer appearance-none"
                                >
                                    <option value="all">전체</option>
                                    <option value="title">제목</option>
                                    <option value="content">내용</option>
                                </select>
                                <input
                                    type="text"
                                    placeholder="무엇을 찾으시나요?"
                                    value={searchInput}
                                    onChange={(e) => setSearchInput(e.target.value)}
                                    className="w-full pl-3 pr-4 py-2.5 text-sm bg-transparent focus:outline-none dark:text-white"
                                />
                                {search && (
                                    <button
                                        type="button"
                                        onClick={clearSearch}
                                        className="p-2 mr-1 text-zinc-400 hover:text-zinc-600 dark:hover:text-zinc-200 transition-colors"
                                    >
                                        <X size={16} />
                                    </button>
                                )}
                            </div>
                        </form>
                    </div>
                </div>

                {isLoggedIn ? (
                    <section>
                        <CreatePostForm onSuccess={refetch} />
                    </section>
                ) : null}

                <nav className="flex items-center gap-1 border-b border-zinc-200 dark:border-zinc-800">
                    {[
                        { id: 'all', label: '전체' },
                        { id: 'free', label: '자유게시판' },
                        { id: 'neighborhood', label: '동네 소식' },
                        { id: 'industry', label: '업종 이야기' },
                        { id: 'notice', label: '공지사항' },
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

                {search && (
                    <div className="flex items-center justify-between py-2 px-1">
                        <div className="flex items-center gap-2">
                            <span className="text-sm text-zinc-500 dark:text-zinc-400">
                                <span className="font-semibold text-blue-600 dark:text-blue-400">&ldquo;{search}&rdquo;</span>에 대한 검색 결과
                            </span>
                            <span className="text-xs px-2 py-0.5 bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 rounded-full font-medium">
                                {posts?.length || 0}건
                            </span>
                        </div>
                        <button
                            onClick={clearSearch}
                            className="text-xs text-zinc-500 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
                        >
                            검색 초기화
                        </button>
                    </div>
                )}

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
                        posts?.map((post) => (
                            <PostCard
                                key={post.id}
                                post={post}
                                onDeleteSuccess={refetch}
                                isHighlighted={String(post.id) === String(targetPostId)}
                                initialShowComments={String(post.id) === String(targetPostId) && !!targetCommentId}
                            />
                        ))
                    )}
                </main>
            </div>
        </div>
    );
}
