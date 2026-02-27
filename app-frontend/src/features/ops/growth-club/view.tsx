import { useEffect, useState, useMemo } from "react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Post, Comment } from "@/features/growth-club/types";
import {
  fetchBlindedPosts,
  unblindPost,
  fetchBlindedComments,
  unblindComment,
  suspendUser,
  unsuspendUser,
  deletePost,
  deleteComment,
} from "./api";
import {
  ShieldAlert, CheckCircle2, RotateCcw, MessageSquare,
  Ban, ShieldCheck, Trash2, Search, RefreshCw, X,
  Eye, FileText, ChevronDown, Users,
} from "lucide-react";

// ─── 미리보기 모달 ────────────────────────────────────────────────────────────
function PreviewModal({
  item,
  type,
  onClose,
}: {
  item: (Post | Comment) & { report_count: number; report_reason?: string };
  type: "post" | "comment";
  onClose: () => void;
}) {
  const isPost = type === "post";
  const post = item as Post;

  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-2xl mx-4 bg-white rounded-3xl shadow-2xl p-8 animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 헤더 */}
        <div className="flex items-start justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-red-50 rounded-xl">
              <ShieldAlert className="h-5 w-5 text-red-500" />
            </div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-0.5">
                {isPost ? "블라인드 게시글" : "블라인드 댓글"} 상세보기
              </p>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-black bg-red-100 text-red-700 px-2 py-0.5 rounded-full">
                  신고 {item.report_count}회
                </span>
                {item.report_reason && (
                  <span className="text-[11px] font-semibold bg-orange-50 text-orange-600 px-2 py-0.5 rounded-full">
                    {item.report_reason}
                  </span>
                )}
              </div>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl hover:bg-slate-100 transition-colors text-slate-400"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* 작성자 정보 */}
        <div className="flex items-center gap-3 mb-5 p-3 bg-slate-50 rounded-2xl">
          <div className="h-9 w-9 rounded-full bg-indigo-100 flex items-center justify-center text-indigo-700 font-black text-sm">
            {item.author?.username?.[0]?.toUpperCase() ?? "?"}
          </div>
          <div>
            <p className="text-sm font-bold text-slate-800">{item.author?.username}</p>
            <p className="text-xs text-slate-400">{item.author?.email || "이메일 없음"}</p>
          </div>
          <div className="ml-auto text-xs text-slate-400">
            {new Date(item.created_at).toLocaleString("ko-KR")}
          </div>
        </div>

        {/* 콘텐츠 */}
        <div className="bg-slate-50 rounded-2xl p-5 max-h-64 overflow-y-auto">
          {isPost && (
            <h3 className="font-bold text-slate-900 text-base mb-3">{post.title}</h3>
          )}
          <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
            {item.content}
          </p>
        </div>

        <p className="mt-4 text-center text-xs text-slate-400">
          ESC 또는 바깥 클릭으로 닫기
        </p>
      </div>
    </div>
  );
}

// ─── 정지 사유 입력 모달 ──────────────────────────────────────────────────────
function SuspensionModal({
  username,
  onClose,
  onConfirm,
}: {
  userId: number;
  username: string;
  targetType: "POST" | "COMMENT";
  onClose: () => void;
  onConfirm: (reason: string) => void;
}) {
  const [reason, setReason] = useState("");

  useEffect(() => {
    const handler = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-[60] flex items-center justify-center bg-black/40 backdrop-blur-sm animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-md mx-4 bg-white rounded-3xl shadow-2xl p-8 animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="p-2 bg-orange-50 rounded-xl">
            <Ban className="h-5 w-5 text-orange-500" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-900">유저 이용 정지</h3>
            <p className="text-sm text-slate-500">{username}님을 정지 처리합니다.</p>
          </div>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
              정지 사유 입력
            </label>
            <textarea
              autoFocus
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="부적절한 게시글 작성 등의 사유를 입력해주세요."
              className="w-full h-32 px-4 py-3 rounded-2xl border border-slate-200 bg-slate-50 text-sm focus:outline-none focus:ring-2 focus:ring-orange-300 transition-all resize-none"
            />
          </div>

          <div className="flex gap-2">
            <button
              onClick={onClose}
              className="flex-1 py-3 rounded-xl bg-slate-100 text-slate-600 font-bold text-sm hover:bg-slate-200 transition-all"
            >
              취소
            </button>
            <button
              disabled={!reason.trim()}
              onClick={() => onConfirm(reason)}
              className="flex-2 px-8 py-3 rounded-xl bg-orange-500 text-white font-bold text-sm hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-lg shadow-orange-200"
            >
              정지하기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── 메인 뷰 ─────────────────────────────────────────────────────────────────
export function OpsGrowthClubView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();
  const [activeTab, setActiveTab] = useState<"posts" | "comments">("posts");
  const [blindedPosts, setBlindedPosts] = useState<Post[]>([]);
  const [blindedComments, setBlindedComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // 정지 상태 추적
  const [suspendedUsers, setSuspendedUsers] = useState<Record<number, boolean>>({});

  // 검색 & 필터
  const [searchQuery, setSearchQuery] = useState("");
  const [reasonFilter, setReasonFilter] = useState("all");

  // 일괄 처리용 선택
  const [selectedPostIds, setSelectedPostIds] = useState<Set<number>>(new Set());
  const [selectedCommentIds, setSelectedCommentIds] = useState<Set<number>>(new Set());

  // 미리보기 모달
  const [previewItem, setPreviewItem] = useState<{
    item: Post | Comment;
    type: "post" | "comment";
  } | null>(null);

  // 정지 모달
  const [suspensionTarget, setSuspensionTarget] = useState<{
    userId: number;
    username: string;
    targetType: "POST" | "COMMENT";
    targetId: number;
  } | null>(null);

  // ── 데이터 로드 ───────────────────────────────────────────────────────────
  const loadData = async (silent = false) => {
    try {
      if (!silent) setIsLoading(true);
      else setIsRefreshing(true);
      const [posts, comments] = await Promise.all([
        fetchBlindedPosts(),
        fetchBlindedComments(),
      ]);
      setBlindedPosts(posts);
      setBlindedComments(comments);
      setSelectedPostIds(new Set());
      setSelectedCommentIds(new Set());
    } catch (err) {
      setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (!canRender) return;
    void loadData();
  }, [canRender]);

  // ── 신고 사유 목록 (동적) ─────────────────────────────────────────────────
  const postReasons = useMemo(() => {
    const reasons = new Set(blindedPosts.map((p) => p.report_reason).filter(Boolean));
    return ["all", ...Array.from(reasons)] as string[];
  }, [blindedPosts]);

  const commentReasons = useMemo(() => {
    const reasons = new Set(blindedComments.map((c) => c.report_reason).filter(Boolean));
    return ["all", ...Array.from(reasons)] as string[];
  }, [blindedComments]);

  // ── 필터링된 목록 ─────────────────────────────────────────────────────────
  const filteredPosts = useMemo(() => {
    return blindedPosts.filter((p) => {
      const matchSearch =
        !searchQuery ||
        p.title?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.author?.username?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchReason =
        reasonFilter === "all" || p.report_reason === reasonFilter;
      return matchSearch && matchReason;
    });
  }, [blindedPosts, searchQuery, reasonFilter]);

  const filteredComments = useMemo(() => {
    return blindedComments.filter((c) => {
      const matchSearch =
        !searchQuery ||
        c.content?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        c.author?.username?.toLowerCase().includes(searchQuery.toLowerCase());
      const matchReason =
        reasonFilter === "all" || c.report_reason === reasonFilter;
      return matchSearch && matchReason;
    });
  }, [blindedComments, searchQuery, reasonFilter]);

  // ── 개별 핸들러 ──────────────────────────────────────────────────────────
  const handleUnblindPost = async (postId: number) => {
    if (!confirm("이 게시글의 블라인드 처리를 해제하시겠습니까? 다시 모든 유저에게 노출됩니다.")) return;
    try {
      await unblindPost(postId);
      void loadData(true);
    } catch {
      alert("해제 중 오류가 발생했습니다.");
    }
  };

  const handleUnblindComment = async (commentId: number) => {
    if (!confirm("이 댓글의 블라인드 처리를 해제하시겠습니까? 다시 모든 유저에게 노출됩니다.")) return;
    try {
      await unblindComment(commentId);
      void loadData(true);
    } catch {
      alert("해제 중 오류가 발생했습니다.");
    }
  };

  const handleSuspendUser = async (userId: number, isSuspended: boolean, targetType: "POST" | "COMMENT" = "POST", targetId: number = 0, username: string = "") => {
    if (isSuspended) {
      if (!confirm("이 유저의 정지 처리를 해제하시겠습니까?")) return;
      try {
        await unsuspendUser(userId);
        setSuspendedUsers((prev) => ({ ...prev, [userId]: false }));
        alert("정지 해제 처리가 완료되었습니다.");
        void loadData(true);
      } catch {
        alert("정지 해제 중 오류가 발생했습니다.");
      }
    } else {
      setSuspensionTarget({ userId, username, targetType, targetId });
    }
  };

  const confirmSuspension = async (reason: string) => {
    if (!suspensionTarget) return;
    try {
      await suspendUser(
        suspensionTarget.userId,
        reason,
        suspensionTarget.targetType,
        suspensionTarget.targetId
      );
      setSuspendedUsers((prev) => ({ ...prev, [suspensionTarget.userId]: true }));
      setSuspensionTarget(null);
      alert("유저 정지 처리가 완료되었습니다.");
      void loadData(true);
    } catch {
      alert("정지 처리 중 오류가 발생했습니다.");
    }
  };

  const handleDeletePost = async (postId: number) => {
    if (!confirm("이 게시글을 영구적으로 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) return;
    try {
      await deletePost(postId);
      void loadData(true);
    } catch {
      alert("삭제 중 오류가 발생했습니다.");
    }
  };

  const handleDeleteComment = async (commentId: number) => {
    if (!confirm("이 댓글을 영구적으로 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.")) return;
    try {
      await deleteComment(commentId);
      void loadData(true);
    } catch {
      alert("삭제 중 오류가 발생했습니다.");
    }
  };

  // ── 일괄 처리 핸들러 ─────────────────────────────────────────────────────
  const handleBulkDeletePosts = async () => {
    if (selectedPostIds.size === 0) return;
    if (!confirm(`선택한 게시글 ${selectedPostIds.size}개를 영구 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return;
    try {
      await Promise.all(Array.from(selectedPostIds).map((id) => deletePost(id)));
      void loadData(true);
    } catch {
      alert("일괄 삭제 중 오류가 발생했습니다.");
    }
  };

  const handleBulkUnblindPosts = async () => {
    if (selectedPostIds.size === 0) return;
    if (!confirm(`선택한 게시글 ${selectedPostIds.size}개의 블라인드를 해제하시겠습니까?`)) return;
    try {
      await Promise.all(Array.from(selectedPostIds).map((id) => unblindPost(id)));
      void loadData(true);
    } catch {
      alert("일괄 블라인드 해제 중 오류가 발생했습니다.");
    }
  };

  const handleBulkDeleteComments = async () => {
    if (selectedCommentIds.size === 0) return;
    if (!confirm(`선택한 댓글 ${selectedCommentIds.size}개를 영구 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`)) return;
    try {
      await Promise.all(Array.from(selectedCommentIds).map((id) => deleteComment(id)));
      void loadData(true);
    } catch {
      alert("일괄 삭제 중 오류가 발생했습니다.");
    }
  };

  const handleBulkUnblindComments = async () => {
    if (selectedCommentIds.size === 0) return;
    if (!confirm(`선택한 댓글 ${selectedCommentIds.size}개의 블라인드를 해제하시겠습니까?`)) return;
    try {
      await Promise.all(Array.from(selectedCommentIds).map((id) => unblindComment(id)));
      void loadData(true);
    } catch {
      alert("일괄 블라인드 해제 중 오류가 발생했습니다.");
    }
  };

  // ── 전체 선택 ────────────────────────────────────────────────────────────
  const allPostsSelected =
    filteredPosts.length > 0 &&
    filteredPosts.every((p) => selectedPostIds.has(p.id));
  const allCommentsSelected =
    filteredComments.length > 0 &&
    filteredComments.every((c) => selectedCommentIds.has(c.id));

  const toggleAllPosts = () => {
    if (allPostsSelected) {
      setSelectedPostIds(new Set());
    } else {
      setSelectedPostIds(new Set(filteredPosts.map((p) => p.id)));
    }
  };

  const toggleAllComments = () => {
    if (allCommentsSelected) {
      setSelectedCommentIds(new Set());
    } else {
      setSelectedCommentIds(new Set(filteredComments.map((c) => c.id)));
    }
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  const currentReasons = activeTab === "posts" ? postReasons : commentReasons;
  const selectedCount = activeTab === "posts" ? selectedPostIds.size : selectedCommentIds.size;

  return (
    <>
      {/* 미리보기 모달 */}
      {previewItem && (
        <PreviewModal
          item={previewItem.item as (Post | Comment) & { report_count: number; report_reason?: string }}
          type={previewItem.type}
          onClose={() => setPreviewItem(null)}
        />
      )}

      {/* 정지 사유 모달 */}
      {suspensionTarget && (
        <SuspensionModal
          userId={suspensionTarget.userId}
          username={suspensionTarget.username}
          targetType={suspensionTarget.targetType}
          onClose={() => setSuspensionTarget(null)}
          onConfirm={confirmSuspension}
        />
      )}

      <div className="space-y-6 pb-20 animate-in fade-in duration-500">
        {/* ── 상단 요약 통계 ── */}
        <div className="grid grid-cols-3 gap-4">
          <StatCard
            label="블라인드 게시글"
            value={blindedPosts.length}
            icon={<FileText className="h-5 w-5" />}
            color="indigo"
          />
          <StatCard
            label="블라인드 댓글"
            value={blindedComments.length}
            icon={<MessageSquare className="h-5 w-5" />}
            color="violet"
          />
          <StatCard
            label="정지된 유저"
            value={
              [...blindedPosts, ...blindedComments].reduce((acc, item) => {
                const id = item.author?.id;
                if (id && item.author?.is_suspended) acc.add(id);
                return acc;
              }, new Set<number>()).size
            }
            icon={<Users className="h-5 w-5" />}
            color="orange"
          />
        </div>

        <section className="rounded-3xl border border-slate-200 bg-white p-8 shadow-sm">
          <header className="mb-6">
            {/* 제목 + 새로고침 */}
            <div className="flex items-center justify-between mb-5">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-red-50 rounded-2xl">
                  <ShieldAlert className="h-6 w-6 text-red-600" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-slate-900 leading-tight">그로스 클럽 관리</h1>
                  <p className="text-sm text-slate-500 font-medium">
                    부적절한 게시글 및 댓글을 관리하고 투명한 커뮤니티를 유지합니다.
                  </p>
                </div>
              </div>
              <button
                onClick={() => void loadData(true)}
                disabled={isRefreshing}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 text-sm font-semibold transition-all border border-slate-200 disabled:opacity-50"
              >
                <RefreshCw className={`h-4 w-4 ${isRefreshing ? "animate-spin" : ""}`} />
                새로고침
              </button>
            </div>

            {/* 탭 */}
            <div className="flex items-center justify-between">
              <div className="flex gap-1 p-1 bg-slate-50 rounded-xl w-fit">
                <TabButton
                  label="블라인드 게시글"
                  count={blindedPosts.length}
                  active={activeTab === "posts"}
                  onClick={() => { setActiveTab("posts"); setSearchQuery(""); setReasonFilter("all"); }}
                />
                <TabButton
                  label="블라인드 댓글"
                  count={blindedComments.length}
                  active={activeTab === "comments"}
                  onClick={() => { setActiveTab("comments"); setSearchQuery(""); setReasonFilter("all"); }}
                />
              </div>
            </div>

            {/* 검색 + 필터 바 */}
            <div className="flex items-center gap-3 mt-4">
              <div className="relative flex-1">
                <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="내용, 작성자 검색..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-300 transition-all"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery("")}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                  >
                    <X className="h-4 w-4" />
                  </button>
                )}
              </div>
              <div className="relative">
                <select
                  value={reasonFilter}
                  onChange={(e) => setReasonFilter(e.target.value)}
                  className="appearance-none pl-4 pr-9 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-300 cursor-pointer font-medium"
                >
                  <option value="all">전체 사유</option>
                  {currentReasons.filter((r) => r !== "all").map((r) => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {/* 일괄 처리 툴바 */}
            {selectedCount > 0 && (
              <div className="flex items-center gap-3 mt-4 p-3 bg-indigo-50 rounded-2xl border border-indigo-100 animate-in slide-in-from-top-1 duration-200">
                <span className="text-sm font-bold text-indigo-700">
                  {selectedCount}개 선택됨
                </span>
                <div className="flex items-center gap-2 ml-auto">
                  {activeTab === "posts" ? (
                    <>
                      <button
                        onClick={handleBulkUnblindPosts}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-indigo-700 text-xs font-bold border border-indigo-200 hover:bg-indigo-100 transition-all"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        일괄 블라인드 해제
                      </button>
                      <button
                        onClick={handleBulkDeletePosts}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500 text-white text-xs font-bold hover:bg-red-600 transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        일괄 삭제
                      </button>
                    </>
                  ) : (
                    <>
                      <button
                        onClick={handleBulkUnblindComments}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white text-indigo-700 text-xs font-bold border border-indigo-200 hover:bg-indigo-100 transition-all"
                      >
                        <RotateCcw className="h-3.5 w-3.5" />
                        일괄 블라인드 해제
                      </button>
                      <button
                        onClick={handleBulkDeleteComments}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-red-500 text-white text-xs font-bold hover:bg-red-600 transition-all"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        일괄 삭제
                      </button>
                    </>
                  )}
                  <button
                    onClick={() => {
                      if (activeTab === "posts") setSelectedPostIds(new Set());
                      else setSelectedCommentIds(new Set());
                    }}
                    className="p-1.5 rounded-lg hover:bg-indigo-100 text-indigo-400 transition-all"
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
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
            /* ── 게시글 탭 ── */
            <div className="animate-in slide-in-from-bottom-2 duration-300">
              {filteredPosts.length === 0 ? (
                <EmptyState
                  icon={<CheckCircle2 />}
                  message={searchQuery || reasonFilter !== "all" ? "검색 결과가 없습니다." : "관리할 게시글이 없습니다."}
                />
              ) : (
                <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-100">
                      <tr>
                        <th className="px-4 py-4">
                          <input
                            type="checkbox"
                            checked={allPostsSelected}
                            onChange={toggleAllPosts}
                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-400 h-4 w-4 cursor-pointer"
                          />
                        </th>
                        <th className="px-6 py-4 font-bold">콘텐츠</th>
                        <th className="px-6 py-4 font-bold">작성자</th>
                        <th className="px-6 py-4 font-bold text-center">신고</th>
                        <th className="px-6 py-4 font-bold text-center">날짜</th>
                        <th className="px-6 py-4 font-bold text-right">조치</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 bg-white">
                      {filteredPosts.map((post) => (
                        <tr
                          key={post.id}
                          className={`hover:bg-slate-50/30 transition-colors group ${selectedPostIds.has(post.id) ? "bg-indigo-50/40" : ""}`}
                        >
                          <td className="px-4 py-5">
                            <input
                              type="checkbox"
                              checked={selectedPostIds.has(post.id)}
                              onChange={() => {
                                setSelectedPostIds((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(post.id)) next.delete(post.id); else next.add(post.id);
                                  return next;
                                });
                              }}
                              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-400 h-4 w-4 cursor-pointer"
                            />
                          </td>
                          <td className="px-6 py-5">
                            <div className="max-w-sm">
                              <h4 className="font-bold text-slate-900 mb-1 group-hover:text-indigo-600 transition-colors line-clamp-1">
                                {post.title}
                              </h4>
                              <p className="text-xs text-slate-500 line-clamp-2 leading-relaxed">{post.content}</p>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex items-center gap-2">
                              <div className="h-7 w-7 rounded-full bg-indigo-50 flex-shrink-0 flex items-center justify-center text-indigo-600 font-black text-xs">
                                {post.author?.username?.[0]?.toUpperCase() ?? "?"}
                              </div>
                              <div>
                                <p className="font-semibold text-slate-700 text-xs">{post.author?.username}</p>
                                {post.author?.is_suspended && (
                                  <span className="text-[9px] font-black text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded-full">
                                    정지됨
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex flex-col items-center gap-1.5">
                              <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ring-1 ${post.report_count >= 10
                                ? "bg-red-200 text-red-800 ring-red-300"
                                : "bg-red-100 text-red-700 ring-red-200"
                                }`}>
                                {post.report_count}회
                              </span>
                              {post.report_reason && (
                                <span className="text-[10px] text-slate-400 font-medium">{post.report_reason}</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-5 text-center text-xs text-slate-500">
                            {new Date(post.created_at).toLocaleDateString("ko-KR")}
                          </td>
                          <td className="px-6 py-5 text-right">
                            <div className="inline-flex items-center gap-1.5 flex-wrap justify-end">
                              {/* 미리보기 */}
                              <button
                                onClick={() => setPreviewItem({ item: post, type: "post" })}
                                className="inline-flex items-center gap-1 rounded-xl bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200 border border-slate-200 transition-all active:scale-95"
                              >
                                <Eye className="h-3.5 w-3.5" />
                              </button>
                              {/* 삭제 */}
                              <button
                                onClick={() => handleDeletePost(post.id)}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-red-100 px-3 py-2 text-xs font-bold text-red-800 hover:bg-red-200 border border-red-200 transition-all active:scale-95"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                삭제
                              </button>
                              {/* 정지 / 해제 */}
                              {(() => {
                                const authorId = post.author?.id;
                                if (!authorId) return null;
                                const isSuspended = suspendedUsers[authorId] !== undefined
                                  ? suspendedUsers[authorId]
                                  : (post.author?.is_suspended ?? false);
                                return isSuspended ? (
                                  <button
                                    onClick={() => handleSuspendUser(authorId, true)}
                                    className="inline-flex items-center gap-1.5 rounded-xl bg-green-100 px-3 py-2 text-xs font-bold text-green-800 hover:bg-green-200 border border-green-200 transition-all active:scale-95"
                                  >
                                    <ShieldCheck className="h-3.5 w-3.5" />
                                    정지 해제
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleSuspendUser(authorId, false, "POST", post.id, post.author?.username || "")}
                                    className="inline-flex items-center gap-1.5 rounded-xl bg-orange-100 px-3 py-2 text-xs font-bold text-orange-800 hover:bg-orange-200 border border-orange-200 transition-all active:scale-95"
                                  >
                                    <Ban className="h-3.5 w-3.5" />
                                    유저 정지
                                  </button>
                                );
                              })()}
                              {/* 블라인드 해제 */}
                              <button
                                onClick={() => handleUnblindPost(post.id)}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all active:scale-95"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                블라인드 해제
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            /* ── 댓글 탭 ── */
            <div className="animate-in slide-in-from-bottom-2 duration-300">
              {filteredComments.length === 0 ? (
                <EmptyState
                  icon={<MessageSquare />}
                  message={searchQuery || reasonFilter !== "all" ? "검색 결과가 없습니다." : "관리할 댓글이 없습니다."}
                />
              ) : (
                <div className="overflow-hidden rounded-2xl border border-slate-100 shadow-[0_4px_20px_-4px_rgba(0,0,0,0.05)]">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-slate-50/80 text-slate-500 border-b border-slate-100">
                      <tr>
                        <th className="px-4 py-4">
                          <input
                            type="checkbox"
                            checked={allCommentsSelected}
                            onChange={toggleAllComments}
                            className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-400 h-4 w-4 cursor-pointer"
                          />
                        </th>
                        <th className="px-6 py-4 font-bold">댓글 내용</th>
                        <th className="px-6 py-4 font-bold">작성자</th>
                        <th className="px-6 py-4 font-bold text-center">신고</th>
                        <th className="px-6 py-4 font-bold text-center">날짜</th>
                        <th className="px-6 py-4 font-bold text-right">조치</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-50 bg-white">
                      {filteredComments.map((comment) => (
                        <tr
                          key={comment.id}
                          className={`hover:bg-slate-50/30 transition-colors group ${selectedCommentIds.has(comment.id) ? "bg-indigo-50/40" : ""}`}
                        >
                          <td className="px-4 py-5">
                            <input
                              type="checkbox"
                              checked={selectedCommentIds.has(comment.id)}
                              onChange={() => {
                                setSelectedCommentIds((prev) => {
                                  const next = new Set(prev);
                                  if (next.has(comment.id)) next.delete(comment.id); else next.add(comment.id);
                                  return next;
                                });
                              }}
                              className="rounded border-slate-300 text-indigo-600 focus:ring-indigo-400 h-4 w-4 cursor-pointer"
                            />
                          </td>
                          <td className="px-6 py-5">
                            <p className="text-sm text-slate-700 max-w-sm line-clamp-2 leading-relaxed">
                              {comment.content}
                            </p>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex items-center gap-2">
                              <div className="h-7 w-7 rounded-full bg-violet-50 flex-shrink-0 flex items-center justify-center text-violet-600 font-black text-xs">
                                {comment.author?.username?.[0]?.toUpperCase() ?? "?"}
                              </div>
                              <div>
                                <p className="font-semibold text-slate-700 text-xs">{comment.author?.username}</p>
                                {comment.author?.is_suspended && (
                                  <span className="text-[9px] font-black text-orange-600 bg-orange-50 px-1.5 py-0.5 rounded-full">
                                    정지됨
                                  </span>
                                )}
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-5">
                            <div className="flex flex-col items-center gap-1.5">
                              <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ring-1 ${(comment.report_count ?? 0) >= 10
                                ? "bg-red-200 text-red-800 ring-red-300"
                                : "bg-red-100 text-red-700 ring-red-200"
                                }`}>
                                {comment.report_count ?? 0}회
                              </span>
                              {comment.report_reason && (
                                <span className="text-[10px] text-slate-400 font-medium">{comment.report_reason}</span>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-5 text-center text-xs text-slate-500">
                            {new Date(comment.created_at).toLocaleDateString("ko-KR")}
                          </td>
                          <td className="px-6 py-5 text-right">
                            <div className="inline-flex items-center gap-1.5 flex-wrap justify-end">
                              {/* 미리보기 */}
                              <button
                                onClick={() => setPreviewItem({ item: comment, type: "comment" })}
                                className="inline-flex items-center gap-1 rounded-xl bg-slate-100 px-3 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200 border border-slate-200 transition-all active:scale-95"
                              >
                                <Eye className="h-3.5 w-3.5" />
                              </button>
                              {/* 삭제 */}
                              <button
                                onClick={() => handleDeleteComment(comment.id)}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-red-100 px-3 py-2 text-xs font-bold text-red-800 hover:bg-red-200 border border-red-200 transition-all active:scale-95"
                              >
                                <Trash2 className="h-3.5 w-3.5" />
                                삭제
                              </button>
                              {/* 정지 / 해제 */}
                              {(() => {
                                const authorId = comment.author?.id;
                                if (!authorId) return null;
                                const isSuspended = suspendedUsers[authorId] !== undefined
                                  ? suspendedUsers[authorId]
                                  : (comment.author?.is_suspended ?? false);
                                return isSuspended ? (
                                  <button
                                    onClick={() => handleSuspendUser(authorId, true)}
                                    className="inline-flex items-center gap-1.5 rounded-xl bg-green-100 px-3 py-2 text-xs font-bold text-green-800 hover:bg-green-200 border border-green-200 transition-all active:scale-95"
                                  >
                                    <ShieldCheck className="h-3.5 w-3.5" />
                                    정지 해제
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleSuspendUser(authorId, false, "COMMENT", comment.id, comment.author?.username || "")}
                                    className="inline-flex items-center gap-1.5 rounded-xl bg-orange-100 px-3 py-2 text-xs font-bold text-orange-800 hover:bg-orange-200 border border-orange-200 transition-all active:scale-95"
                                  >
                                    <Ban className="h-3.5 w-3.5" />
                                    유저 정지
                                  </button>
                                );
                              })()}
                              {/* 블라인드 해제 */}
                              <button
                                onClick={() => handleUnblindComment(comment.id)}
                                className="inline-flex items-center gap-1.5 rounded-xl bg-indigo-600 px-3 py-2 text-xs font-bold text-white hover:bg-indigo-700 shadow-md shadow-indigo-200 transition-all active:scale-95"
                              >
                                <RotateCcw className="h-3.5 w-3.5" />
                                블라인드 해제
                              </button>
                            </div>
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
    </>
  );
}

// ─── 소형 컴포넌트들 ──────────────────────────────────────────────────────────
function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string;
  value: number;
  icon: React.ReactNode;
  color: "indigo" | "violet" | "orange";
}) {
  const colorMap = {
    indigo: "bg-indigo-50 text-indigo-600 border-indigo-100",
    violet: "bg-violet-50 text-violet-600 border-violet-100",
    orange: "bg-orange-50 text-orange-600 border-orange-100",
  };
  const numColor = {
    indigo: "text-indigo-700",
    violet: "text-violet-700",
    orange: "text-orange-700",
  };
  return (
    <div className={`rounded-2xl border p-5 flex items-center gap-4 ${colorMap[color]}`}>
      <div className="p-2.5 rounded-xl bg-white/60">{icon}</div>
      <div>
        <p className="text-xs font-semibold text-slate-500 mb-0.5">{label}</p>
        <p className={`text-2xl font-black ${numColor[color]}`}>{value}</p>
      </div>
    </div>
  );
}

function TabButton({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={`px-5 py-2.5 rounded-lg text-sm font-bold transition-all flex items-center gap-2 ${active
        ? "bg-white text-indigo-600 shadow-sm ring-1 ring-slate-200"
        : "text-slate-500 hover:text-slate-700"
        }`}
    >
      {label}
      <span className={`px-1.5 py-0.5 rounded-md text-[10px] ${active ? "bg-indigo-50 text-indigo-600" : "bg-slate-200 text-slate-500"
        }`}>
        {count}
      </span>
    </button>
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
