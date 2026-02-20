'use client';

import React, { useState } from 'react';
import { Comment } from '../types';
import { useAuth } from '@/providers/AuthProvider';
import { growthClubApi } from '../api';
import { CornerDownRight } from 'lucide-react';

interface CommentSectionProps {
    postId: number;
    initialComments: Comment[];
    onCommentAdded: () => void;
}

const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (diffInSeconds < 60) return '방금 전';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}분 전`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}시간 전`;
    return date.toLocaleDateString('ko-KR');
};

export const CommentSection: React.FC<CommentSectionProps> = ({ postId, initialComments, onCommentAdded }) => {
    const { isLoggedIn, user } = useAuth();
    const [newComment, setNewComment] = useState('');
    const [replyTo, setReplyTo] = useState<number | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    // 댓글 계층 구조 형성 (부모/자식 분리)
    const rootComments = initialComments.filter(c => !c.parent_id);
    const replies = initialComments.filter(c => c.parent_id);

    const handleSubmit = async (e: React.FormEvent<HTMLFormElement>, parentId?: number) => {
        e.preventDefault();
        const content = parentId
            ? String(new FormData(e.currentTarget).get('replyContent') ?? '')
            : newComment;

        if (!content.trim()) return;
        if (!isLoggedIn) {
            alert('로그인이 필요한 기능입니다.');
            return;
        }

        setIsSubmitting(true);
        try {
            await growthClubApi.addComment(postId, content, parentId);
            if (!parentId) setNewComment('');
            setReplyTo(null);
            onCommentAdded();
        } catch {
            alert('댓글 작성에 실패했습니다.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleDelete = async (commentId: number) => {
        if (!window.confirm('댓글을 삭제하시겠습니까?')) return;

        setIsSubmitting(true);
        try {
            await growthClubApi.deleteComment(commentId);
            onCommentAdded();
        } catch {
            alert('댓글 삭제에 실패했습니다.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const CommentItem = ({ comment, isReply = false }: { comment: Comment, isReply?: boolean }) => (
        <div className={`group ${isReply ? 'ml-8 mt-3' : 'mt-6 border-b border-zinc-50 dark:border-zinc-800 pb-4'}`}>
            <div className="flex items-start gap-3">
                {isReply && <CornerDownRight className="text-zinc-300 mt-1" size={16} />}
                <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-bold text-zinc-900 dark:text-white">
                                {comment.author?.username || '알 수 없음'}
                            </span>
                            <span className="text-[10px] text-zinc-400">
                                {formatTimeAgo(comment.created_at)}
                            </span>
                        </div>
                        <div className="flex items-center gap-2">
                            {!isReply && isLoggedIn && (
                                <button
                                    onClick={() => setReplyTo(replyTo === comment.id ? null : comment.id)}
                                    className="text-[10px] text-blue-500 hover:text-blue-600 font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    답글 달기
                                </button>
                            )}
                            {isLoggedIn && user && Number(user.id) === comment.author?.id && (
                                <button
                                    onClick={() => handleDelete(comment.id)}
                                    className="text-[10px] text-red-400 hover:text-red-500 font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                                >
                                    삭제
                                </button>
                            )}
                        </div>
                    </div>
                    <p className="text-sm text-zinc-600 dark:text-zinc-400 whitespace-pre-wrap leading-relaxed">
                        {comment.content}
                    </p>

                    {/* 답글 입력창 */}
                    {replyTo === comment.id && (
                        <form onSubmit={(e) => handleSubmit(e, comment.id)} className="mt-4">
                            <div className="flex flex-col gap-2">
                                <textarea
                                    name="replyContent"
                                    placeholder="답글을 남겨보세요..."
                                    className="w-full px-4 py-2.5 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-sm focus:ring-1 focus:ring-blue-500 transition-all outline-none resize-none"
                                    rows={2}
                                    required
                                />
                                <div className="flex justify-end gap-2">
                                    <button
                                        type="button"
                                        onClick={() => setReplyTo(null)}
                                        className="px-3 py-1.5 text-xs text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-700 rounded-md transition-colors"
                                    >
                                        취소
                                    </button>
                                    <button
                                        type="submit"
                                        disabled={isSubmitting}
                                        className="px-3 py-1.5 text-xs bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 transition-colors"
                                    >
                                        답글 등록
                                    </button>
                                </div>
                            </div>
                        </form>
                    )}

                    {/* 이 댓글에 대한 답글들 */}
                    {replies.filter(r => r.parent_id === comment.id).map(reply => (
                        <CommentItem key={reply.id} comment={reply} isReply />
                    ))}
                </div>
            </div>
        </div>
    );

    return (
        <div className="mt-8 pt-8 border-t border-zinc-100 dark:border-zinc-800">
            <h4 className="text-sm font-bold text-zinc-900 dark:text-white mb-6 flex items-center gap-2">
                댓글 <span className="text-blue-500">{initialComments.length}</span>
            </h4>

            {/* 댓글 작성창 */}
            <form onSubmit={(e) => handleSubmit(e)} className="mb-8">
                <div className="relative">
                    <textarea
                        value={newComment}
                        onChange={(e) => setNewComment(e.target.value)}
                        placeholder={isLoggedIn ? "커뮤니티 가이드를 준수하는 따뜻한 댓글을 남겨주세요." : "로그인 후 댓글을 남길 수 있습니다."}
                        disabled={!isLoggedIn}
                        className="w-full px-4 py-3 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-xl text-sm focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all outline-none resize-none"
                        rows={3}
                    />
                    {isLoggedIn && (
                        <div className="absolute bottom-3 right-3">
                            <button
                                type="submit"
                                disabled={isSubmitting || !newComment.trim()}
                                className="px-4 py-1.5 bg-blue-600 text-white text-xs font-bold rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:bg-zinc-400 transition-all shadow-sm"
                            >
                                등록
                            </button>
                        </div>
                    )}
                </div>
            </form>

            {/* 댓글 목록 */}
            <div className="space-y-2">
                {rootComments.length > 0 ? (
                    rootComments.map(comment => (
                        <CommentItem key={comment.id} comment={comment} />
                    ))
                ) : (
                    <div className="py-10 text-center">
                        <p className="text-sm text-zinc-400">첫 번째 댓글의 주인공이 되어보세요!</p>
                    </div>
                )}
            </div>
        </div>
    );
};
