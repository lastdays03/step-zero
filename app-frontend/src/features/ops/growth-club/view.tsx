"use client";

import { useEffect, useState } from "react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Post, Comment } from "@/features/growth-club/types";
import { fetchBlindedPosts, unblindPost, fetchBlindedComments, unblindComment } from "./api";
import { ShieldAlert, CheckCircle2, RotateCcw, MessageSquare } from "lucide-react";

export function OpsGrowthClubView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();
  const [activeTab, setActiveTab] = useState<"posts" | "comments">("posts");
  const [blindedPosts, setBlindedPosts] = useState<Post[]>([]);
  const [blindedComments, setBlindedComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [posts, comments] = await Promise.all([
        fetchBlindedPosts(),
        fetchBlindedComments()
      ]);
      setBlindedPosts(posts);
      setBlindedComments(comments);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!canRender) return;
    void loadData();
  }, [canRender]);

  const handleUnblindPost = async (postId: number) => {
    if (!confirm("이 게시글의 블라인드 처리를 해제하시겠습니까? 다시 모든 유저에게 노출됩니다.")) return;
    try {
      await unblindPost(postId);
      alert("공개 처리가 완료되었습니다.");
      void loadData();
    } catch (err) {
      alert("해제 중 오류가 발생했습니다.");
    }
  };

  const handleUnblindComment = async (commentId: number) => {
    if (!confirm("이 댓글의 블라인드 처리를 해제하시겠습니까? 다시 모든 유저에게 노출됩니다.")) return;
    try {
      await unblindComment(commentId);
      alert("공개 처리가 완료되었습니다.");
      void loadData();
    } catch (err) {
      alert("해제 중 오류가 발생했습니다.");
    }
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  return (
    <div className="space-y-6 pb-20 animate-in fade-in duration-500">
      <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2.5 bg-red-50 rounded-2xl">
              <ShieldAlert className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 leading-tight">그로스 클럽 관리</h1>
              <p className="text-sm text-slate-500 font-medium">부적절한 게시글 및 댓글을 관리하고 투명한 커뮤니티를 유지합니다.</p>
            </div>
          </div>

          {/* 카테고리 탭 시스템 */}
          <div className="flex gap-1 p-1 bg-slate-50 rounded-xl w-fit">
            <button
              onClick={() => setActiveTab("posts")}
              className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${activeTab === "posts"
                  ? "bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200"
                  : "text-slate-500 hover:text-slate-700"
                }`}
            >
              블라인드 게시글
              <span className={`px-1.5 py-0.5 rounded-md text-[10px] ${activeTab === "posts" ? "bg-indigo-50 text-indigo-600" : "bg-slate-200 text-slate-500"
                }`}>
                {blindedPosts.length}
              </span>
            </button>
            <button
              onClick={() => setActiveTab("comments")}
              className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${activeTab === "comments"
                  ? "bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200"
                  : "text-slate-500 hover:text-slate-700"
                }`}
            >
              블라인드 댓글
              <span className={`px-1.5 py-0.5 rounded-md text-[10px] ${activeTab === "comments" ? "bg-indigo-50 text-indigo-600" : "bg-slate-200 text-slate-500"
                }`}>
                {blindedComments.length}
              </span>
            </button>
          </div>
        </header>

        {isLoading ? (
          <div className="flex h-64 flex-col items-center justify-center gap-4">
            <div className="h-10 w-10 animate-spin rounded-full border-4 border-slate-100 border-t-indigo-600" />
            <p className="text-slate-400 text-sm font-medium">데이터를 불러오는 중입니다...</p>
          </div>
        ) : error ? (
          <div className="rounded-2xl bg-red-50 p-6 flex items-center gap-4">
            <ShieldAlert className="h-8 w-8 text-red-500" />
            <div>
              <h3 className="font-bold text-red-900">오류가 발생했습니다</h3>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        ) : activeTab === "posts" ? (
          /* 게시글 렌더링 */
          <div className="animate-in slide-in-from-bottom-2 duration-300">
            {blindedPosts.length === 0 ? (
              <EmptyState icon={<CheckCircle2 />} message="관리할 게시글이 없습니다." />
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 font-bold">콘텐츠</th>
                      <th className="px-6 py-4 font-bold">작성자</th>
                      <th className="px-6 py-4 font-bold text-center">신고</th>
                      <th className="px-6 py-4 font-bold text-center">날짜</th>
                      <th className="px-6 py-4 font-bold text-right">조치</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 bg-white">
                    {blindedPosts.map((post) => (
                      <tr key={post.id} className="hover:bg-slate-50/30 transition-colors group">
                        <td className="px-6 py-5">
                          <div className="max-w-md">
                            <h4 className="font-bold text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors line-clamp-1">
                              {post.title}
                            </h4>
                            <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{post.content}</p>
                          </div>
                        </td>
                        <td className="px-6 py-5 font-semibold text-slate-700">
                          {post.author.username}
                        </td>
                        <td className="px-6 py-5">
                          <div className="flex flex-col items-center gap-1.5">
                            <span className="text-[10px] font-black bg-red-100 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">
                              {post.report_count}회
                            </span>
                            <span className="text-[10px] text-slate-400 font-medium">
                              {post.report_reason || "일반신고"}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-5 text-center text-xs text-slate-500">
                          {new Date(post.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-5 text-right">
                          <button
                            onClick={() => handleUnblindPost(post.id)}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all active:scale-95"
                          >
                            <RotateCcw className="h-3.5 w-3.5" />
                            블라인드 해제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        ) : (
          /* 댓글 렌더링 */
          <div className="animate-in slide-in-from-bottom-2 duration-300">
            {blindedComments.length === 0 ? (
              <EmptyState icon={<MessageSquare />} message="관리할 댓글이 없습니다." />
            ) : (
              <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-100">
                    <tr>
                      <th className="px-6 py-4 font-bold">댓글 내용</th>
                      <th className="px-6 py-4 font-bold">작성자</th>
                      <th className="px-6 py-4 font-bold text-center">신고</th>
                      <th className="px-6 py-4 font-bold text-center">날짜</th>
                      <th className="px-6 py-4 font-bold text-right">조치</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-50 bg-white">
                    {blindedComments.map((comment) => (
                      <tr key={comment.id} className="hover:bg-slate-50/30 transition-colors group">
                        <td className="px-6 py-5">
                          <p className="text-sm text-slate-700 max-w-md line-clamp-2 leading-relaxed">
                            {comment.content}
                          </p>
                        </td>
                        <td className="px-6 py-5 font-semibold text-slate-700">
                          {comment.author.username}
                        </td>
                        <td className="px-6 py-5">
                          <div className="flex flex-col items-center gap-1.5">
                            <span className="text-[10px] font-black bg-red-100 text-red-700 px-2 py-0.5 rounded-full ring-1 ring-red-200">
                              {comment.report_count}회
                            </span>
                            <span className="text-[10px] text-slate-400 font-medium">
                              {comment.report_reason || "일반신고"}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-5 text-center text-xs text-slate-500">
                          {new Date(comment.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-5 text-right">
                          <button
                            onClick={() => handleUnblindComment(comment.id)}
                            className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-4 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all active:scale-95"
                          >
                            <RotateCcw className="h-3.5 w-3.5" />
                            블라인드 해제
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function EmptyState({ icon, message }: { icon: React.ReactNode; message: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-slate-300">
      <div className="mb-4 scale-150 opacity-20">{icon}</div>
      <p className="text-sm font-bold text-slate-400">{message}</p>
    </div>
  );
}
