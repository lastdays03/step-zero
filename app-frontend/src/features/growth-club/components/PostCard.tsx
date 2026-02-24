'use client';

import React, { useState } from 'react';
import { Post } from '../types';
import { MessageSquare, ThumbsUp, Trash2, AlertCircle, Paperclip } from 'lucide-react';

import { useAuth } from '@/providers/AuthProvider';
import { growthClubApi } from '../api';
import { CommentSection } from './CommentSection';
import { resolveUploadUrl } from '../utils/upload-url';
import { useTimeAgo } from '../hooks/useTimeAgo';

interface PostCardProps {
    post: Post;
    onDeleteSuccess?: () => void;
    onReportSuccess?: () => void;
}



export const PostCard: React.FC<PostCardProps> = ({ post, onDeleteSuccess, onReportSuccess }) => {
    const { user } = useAuth();
    const [isDeleting, setIsDeleting] = useState(false);
    const [showComments, setShowComments] = useState(false);
    const [isReportModalOpen, setIsReportModalOpen] = useState(false);
    const timeAgo = useTimeAgo(post.created_at);

    // 좋아요 상태 관리를 위한 로컬 스테이트
    const [liked, setLiked] = useState(post.is_liked);
    const [likesCount, setLikesCount] = useState(post.likes_count);
    const [isLiking, setIsLiking] = useState(false);
    const attachments = post.attachments ?? [];
    const imageAttachments = attachments.filter((it) => it.kind === "image");
    const fileAttachments = attachments.filter((it) => it.kind === "file");

    const isAuthor = user && String(user.id) === String(post.author_id);

    const handleDelete = async () => {
        if (!window.confirm('정말 이 게시글을 삭제하시겠습니까?')) return;

        setIsDeleting(true);
        try {
            await growthClubApi.deletePost(post.id);
            if (onDeleteSuccess) {
                onDeleteSuccess();
            }
        } catch (error) {
            console.error('Failed to delete post:', error);
            alert('게시글 삭제에 실패했습니다.');
        } finally {
            setIsDeleting(false);
        }
    };

    const handleReport = () => {
        setIsReportModalOpen(true);
    };

    const submitReport = async (reason: string) => {
        setIsReportModalOpen(false);
        try {
            const result = await growthClubApi.reportPost(post.id, reason);
            alert(result.message);
            if (result.is_blinded && onDeleteSuccess) {
                onDeleteSuccess();
            } else if (onReportSuccess) {
                onReportSuccess();
            }
        } catch (error: any) {
            console.error('Failed to report post:', error);
            const message = error.response?.data?.detail || '게시글 신고에 실패했습니다.';
            alert(message);
        }
    };

    const handleLike = async () => {
        if (!user) {
            alert('좋아요를 누르려면 먼저 로그인해주세요.');
            return;
        }
        if (isLiking) return;

        // 낙관적 업데이트
        const prevLiked = liked;
        const prevCount = likesCount;
        setLiked(!prevLiked);
        setLikesCount(prevLiked ? prevCount - 1 : prevCount + 1);
        setIsLiking(true);

        try {
            const result = await growthClubApi.likePost(post.id);
            // 실제 데이터로 동기화
            setLiked(result.liked);
            setLikesCount(result.likes_count);
        } catch (error) {
            console.error('Failed to like post:', error);
            // 에러 시 롤백
            setLiked(prevLiked);
            setLikesCount(prevCount);
        } finally {
            setIsLiking(false);
        }
    };

    return (
        <article id={`post-${post.id}`} className={`bg-white dark:bg-zinc-900 rounded-xl shadow-sm border border-zinc-200 dark:border-zinc-800 p-6 transition-all hover:shadow-md ${isDeleting ? 'opacity-50 pointer-events-none' : ''}`}>
            <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full overflow-hidden bg-blue-100 flex items-center justify-center text-blue-600 font-bold border border-zinc-100 dark:border-zinc-800">
                        {post.author.profile_img && post.author.profile_img !== 'default.png' ? (
                            <img
                                src={resolveUploadUrl(post.author.profile_img)}
                                alt={post.author.username}
                                className="w-full h-full object-cover"
                                onError={(e) => {
                                    // Fallback if image fails to load
                                    (e.target as HTMLImageElement).style.display = 'none';
                                    (e.target as HTMLImageElement).parentElement!.innerText = post.author.username[0] || '?';
                                }}
                            />
                        ) : (
                            post.author.username[0] || '?'
                        )}
                    </div>
                    <div>
                        <h3 className="text-sm font-semibold text-zinc-900 dark:text-white">{post.author.username}</h3>
                        <p className="text-xs text-zinc-500">
                            {timeAgo} · {post.neighborhood}
                        </p>
                    </div>
                </div>

                {(isAuthor || user?.is_superuser) && (
                    <button
                        onClick={handleDelete}
                        className="p-2 text-zinc-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                        title="게시글 삭제"
                    >
                        <Trash2 size={18} />
                    </button>
                )}
            </div>

            <div className="flex gap-2 mb-4">
                <span className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-[10px] font-bold rounded">
                    {post.neighborhood}
                </span>
                <span className="px-2 py-1 bg-orange-50 dark:bg-orange-900/30 text-orange-600 dark:text-orange-400 text-[10px] font-bold rounded">
                    {post.industry}
                </span>
            </div>

            <h2 className="text-xl font-bold text-zinc-900 dark:text-white mb-2">{post.title}</h2>
            <p className="text-zinc-600 dark:text-zinc-400 text-sm leading-relaxed mb-4 whitespace-pre-wrap">
                {post.content}
            </p>

            {imageAttachments.length > 0 && (
                <div className="mb-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {imageAttachments.map((attachment) => (
                        <div key={attachment.id} className="rounded-lg overflow-hidden border border-zinc-100 dark:border-zinc-800">
                            <img
                                src={resolveUploadUrl(attachment.object_key)}
                                alt={attachment.original_filename || "Post content"}
                                className="w-full object-cover max-h-96"
                            />
                        </div>
                    ))}
                </div>
            )}

            {fileAttachments.length > 0 && (
                <div className="mb-4 flex flex-col gap-2">
                    {fileAttachments.map((attachment) => (
                        <a
                            key={attachment.id}
                            href={resolveUploadUrl(attachment.object_key)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-2 px-3 py-2 bg-zinc-50 dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-lg text-xs text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-700 transition-colors"
                        >
                            <Paperclip size={14} />
                            <span>{attachment.original_filename || "첨부 파일 다운로드"}</span>
                        </a>
                    ))}
                </div>
            )}


            <div className="flex items-center gap-6 pt-4 border-t border-zinc-100 dark:border-zinc-800">
                <button
                    onClick={handleLike}
                    disabled={isLiking}
                    className={`flex items-center gap-2 text-sm transition-colors ${liked ? 'text-blue-600' : 'text-zinc-500 hover:text-blue-600'}`}
                >
                    <ThumbsUp size={18} fill={liked ? "currentColor" : "none"} />
                    <span>좋아요 {likesCount > 0 ? likesCount : ''}</span>
                </button>
                <button
                    onClick={() => setShowComments(!showComments)}
                    className={`flex items-center gap-2 text-sm transition-colors ${showComments ? 'text-blue-600 font-bold' : 'text-zinc-500 hover:text-blue-600'}`}
                >
                    <MessageSquare size={18} />
                    <span>댓글 {post.comments.length}</span>
                </button>
                {!isAuthor && (
                    <button
                        onClick={handleReport}
                        className="flex items-center gap-2 text-zinc-500 hover:text-red-500 text-sm ml-auto"
                        title="게시글 신고"
                    >
                        <AlertCircle size={18} />
                        <span>신고</span>
                    </button>
                )}
            </div>

            {showComments && (
                <CommentSection
                    postId={post.id}
                    initialComments={post.comments}
                    onCommentAdded={onDeleteSuccess || (() => { })}
                />
            )}

            {isReportModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
                    <div className="bg-white dark:bg-zinc-900 rounded-xl max-w-sm w-full p-6 shadow-xl border border-zinc-200 dark:border-zinc-800">
                        <h3 className="text-lg font-bold mb-4 text-zinc-900 dark:text-white">신고 사유 선택</h3>
                        <div className="space-y-2">
                            <button onClick={() => submitReport('욕설과폭언')} className="w-full text-left p-3 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-zinc-700 dark:text-zinc-300">
                                🤬 욕설과폭언
                            </button>
                            <button onClick={() => submitReport('광고')} className="w-full text-left p-3 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-zinc-700 dark:text-zinc-300">
                                📢 광고
                            </button>
                            <button onClick={() => submitReport('기타')} className="w-full text-left p-3 rounded-lg border border-zinc-200 dark:border-zinc-700 hover:bg-zinc-50 dark:hover:bg-zinc-800 transition-colors text-zinc-700 dark:text-zinc-300">
                                기타 불건전한 내용
                            </button>
                        </div>
                        <button onClick={() => setIsReportModalOpen(false)} className="mt-4 w-full p-3 font-semibold text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800 rounded-lg transition-colors">
                            취소
                        </button>
                    </div>
                </div>
            )}
        </article>
    );
};
