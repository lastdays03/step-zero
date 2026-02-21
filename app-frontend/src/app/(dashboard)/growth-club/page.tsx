'use client';

import React, { useState } from 'react';
import { PostCard, CreatePostForm } from '@/features/growth-club';
import { usePosts } from '@/features/growth-club';
import { useAuth } from '@/providers/AuthProvider';
import { Search, ChevronDown } from 'lucide-react';

export default function GrowthClubPage() {
    const { isLoggedIn } = useAuth();
    const [category, setCategory] = useState('all');
    const [search, setSearch] = useState('');
    const [searchType, setSearchType] = useState('all');
    const { posts, isLoading, error, refetch } = usePosts(category, search, searchType);

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        refetch();
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
                    {/* 게시물 작성 버튼/폼 공간의 상단/우측에 검색창 배치 */}
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
                                    <option value="tag">태그</option>
                                </select>
                                <input
                                    type="text"
                                    placeholder="무엇을 찾으시나요?"
                                    value={search}
                                    onChange={(e) => setSearch(e.target.value)}
                                    className="w-full pl-3 pr-4 py-2.5 text-sm bg-transparent focus:outline-none dark:text-white"
                                />
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
