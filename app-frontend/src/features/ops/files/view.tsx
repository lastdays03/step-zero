"use client";

import { useCallback, useEffect, useState } from "react";

import {
  AlertCircle,
  FileText,
  HardDrive,
  Image as ImageIcon,
  Loader2,
  Search,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

import { deleteFile, deleteFiles, fetchFiles, fetchFileStats } from "./api";
import type {
  OpsFile,
  OpsFileListParams,
  OpsFileStats,
} from "./types";

/* ── Helpers ──────────────────────────────────────── */

function formatBytes(bytes: number | null): string {
  if (bytes === null || bytes === 0) return "0 B";
  const k = 1024;
  const sizes = ["B", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`;
}

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleDateString("ko-KR", {
    month: "2-digit",
    day: "2-digit",
  });
}

const OWNER_LABELS: Record<string, string> = {
  actionkit_item: "AK",
  growth_club_post: "GC",
  user_profile: "PR",
};

const OWNER_COLORS: Record<string, string> = {
  actionkit_item: "bg-blue-100 text-blue-700",
  growth_club_post: "bg-green-100 text-green-700",
  user_profile: "bg-purple-100 text-purple-700",
};

function getMimeGroup(mimeType: string | null): string {
  if (!mimeType) return "other";
  if (mimeType.startsWith("image/")) return "image";
  if (
    mimeType.startsWith("application/pdf") ||
    mimeType.startsWith("application/msword") ||
    mimeType.startsWith("application/vnd.openxmlformats") ||
    mimeType.startsWith("text/")
  )
    return "document";
  return "other";
}

const MIME_LABELS: Record<string, string> = {
  image: "이미지",
  document: "문서",
  other: "기타",
};

const MIME_BADGE_COLORS: Record<string, string> = {
  image: "bg-amber-100 text-amber-700",
  document: "bg-sky-100 text-sky-700",
  other: "bg-slate-100 text-slate-600",
};

/* ── Component ────────────────────────────────────── */

export function OpsFilesView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [files, setFiles] = useState<OpsFile[]>([]);
  const [stats, setStats] = useState<OpsFileStats | null>(null);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [search, setSearch] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [ownerType, setOwnerType] = useState("");
  const [mimeGroup, setMimeGroup] = useState("");

  // Selection
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Debounce search
  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  const loadFiles = useCallback(async () => {
    if (!canRender) return;
    setIsLoading(true);
    setError(null);
    try {
      const params: OpsFileListParams = { page, page_size: pageSize };
      if (debouncedSearch) params.search = debouncedSearch;
      if (ownerType) params.owner_type = ownerType;
      if (mimeGroup)
        params.mime_group = mimeGroup as "image" | "document" | "other";
      const res = await fetchFiles(params);
      setFiles(res.data);
      setTotal(res.total);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "파일 목록을 불러오지 못했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, [canRender, page, pageSize, debouncedSearch, ownerType, mimeGroup]);

  const loadStats = useCallback(async () => {
    if (!canRender) return;
    try {
      setStats(await fetchFileStats());
    } catch {
      /* stats failure is non-critical */
    }
  }, [canRender]);

  useEffect(() => {
    void loadFiles();
  }, [loadFiles]);

  useEffect(() => {
    void loadStats();
  }, [loadStats]);

  // Reset page on filter change
  useEffect(() => {
    setPage(1);
    setSelectedIds(new Set());
  }, [debouncedSearch, ownerType, mimeGroup]);

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  const toggleSelect = (id: number) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (selectedIds.size === files.length) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(files.map((f) => f.id)));
    }
  };

  const handleDeleteSingle = async (id: number) => {
    if (!confirm("이 파일을 삭제하시겠습니까?")) return;
    try {
      await deleteFile(id);
      setSelectedIds((prev) => {
        const next = new Set(prev);
        next.delete(id);
        return next;
      });
      void loadFiles();
      void loadStats();
    } catch {
      alert("파일 삭제에 실패했습니다.");
    }
  };

  const handleBatchDelete = async () => {
    setIsDeleting(true);
    try {
      const result = await deleteFiles([...selectedIds]);
      setDeleteDialogOpen(false);
      setSelectedIds(new Set());
      if (result.failed > 0) {
        alert(
          `${result.deleted}개 삭제됨, ${result.failed}개 실패`,
        );
      }
      void loadFiles();
      void loadStats();
    } catch {
      alert("일괄 삭제에 실패했습니다.");
    } finally {
      setIsDeleting(false);
    }
  };

  const resetFilters = () => {
    setSearch("");
    setOwnerType("");
    setMimeGroup("");
  };

  // Stats helpers
  const imageStats = stats?.by_mime_group.find(
    (g) => g.mime_group === "image",
  );
  const docStats = stats?.by_mime_group.find(
    (g) => g.mime_group === "document",
  );

  return (
    <section className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">통합 파일 관리</h1>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardContent className="p-4">
              <p className="text-xs font-medium text-muted-foreground">
                총 파일 수
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {stats.total_files.toLocaleString()}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  개
                </span>
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <p className="text-xs font-medium text-muted-foreground">
                총 용량
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {formatBytes(stats.total_bytes)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-1.5">
                <ImageIcon className="h-3.5 w-3.5 text-amber-600" />
                <p className="text-xs font-medium text-muted-foreground">
                  이미지
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {imageStats?.count ?? 0}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  개
                </span>
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-4">
              <div className="flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5 text-sky-600" />
                <p className="text-xs font-medium text-muted-foreground">
                  문서
                </p>
              </div>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {docStats?.count ?? 0}
                <span className="ml-1 text-sm font-normal text-muted-foreground">
                  개
                </span>
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            placeholder="파일명 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        <select
          value={ownerType}
          onChange={(e) => setOwnerType(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
        >
          <option value="">전체 소유</option>
          <option value="actionkit_item">액션키트</option>
          <option value="growth_club_post">그로스클럽</option>
          <option value="user_profile">프로필</option>
        </select>
        <select
          value={mimeGroup}
          onChange={(e) => setMimeGroup(e.target.value)}
          className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700"
        >
          <option value="">전체 타입</option>
          <option value="image">이미지</option>
          <option value="document">문서</option>
          <option value="other">기타</option>
        </select>
        <Button variant="outline" size="sm" onClick={resetFilters}>
          초기화
        </Button>
      </div>

      {/* Error */}
      {error && (
        <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
          <AlertCircle className="h-4 w-4" />
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="flex items-center justify-center py-12 text-slate-500">
          <Loader2 className="mr-2 h-5 w-5 animate-spin" />
          파일 목록을 불러오는 중...
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && (
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-medium text-slate-500">
                  <th className="p-3 w-10">
                    <Checkbox
                      checked={
                        files.length > 0 && selectedIds.size === files.length
                      }
                      onCheckedChange={toggleAll}
                    />
                  </th>
                  <th className="p-3 w-12">미리보기</th>
                  <th className="p-3">파일명</th>
                  <th className="p-3 w-20">타입</th>
                  <th className="p-3 w-24">크기</th>
                  <th className="p-3 w-16">소유</th>
                  <th className="p-3 w-20">날짜</th>
                  <th className="p-3 w-16">액션</th>
                </tr>
              </thead>
              <tbody>
                {files.length === 0 ? (
                  <tr>
                    <td
                      colSpan={8}
                      className="p-8 text-center text-slate-400"
                    >
                      <HardDrive className="mx-auto mb-2 h-8 w-8" />
                      파일이 없습니다.
                    </td>
                  </tr>
                ) : (
                  files.map((file) => {
                    const group = getMimeGroup(file.mime_type);
                    const isImage = group === "image";
                    return (
                      <tr
                        key={file.id}
                        className="border-b border-slate-100 hover:bg-slate-50"
                      >
                        <td className="p-3">
                          <Checkbox
                            checked={selectedIds.has(file.id)}
                            onCheckedChange={() => toggleSelect(file.id)}
                          />
                        </td>
                        <td className="p-3">
                          {isImage ? (
                            <img
                              src={file.public_url}
                              alt=""
                              className="h-8 w-8 rounded object-cover"
                            />
                          ) : (
                            <div className="flex h-8 w-8 items-center justify-center rounded bg-slate-100">
                              <FileText className="h-4 w-4 text-slate-400" />
                            </div>
                          )}
                        </td>
                        <td className="p-3 max-w-[200px] truncate font-medium text-slate-800">
                          {file.original_filename ??
                            file.object_key.split("/").pop()}
                        </td>
                        <td className="p-3">
                          <span
                            className={`inline-block rounded-full px-2 py-0.5 text-[10px] font-medium ${MIME_BADGE_COLORS[group]}`}
                          >
                            {MIME_LABELS[group]}
                          </span>
                        </td>
                        <td className="p-3 text-slate-600">
                          {formatBytes(file.size_bytes)}
                        </td>
                        <td className="p-3">
                          <Badge
                            variant="secondary"
                            className={
                              OWNER_COLORS[file.owner_type] ?? ""
                            }
                          >
                            {OWNER_LABELS[file.owner_type] ??
                              file.owner_type}
                          </Badge>
                        </td>
                        <td className="p-3 text-slate-500">
                          {formatDate(file.uploaded_at)}
                        </td>
                        <td className="p-3">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteSingle(file.id)}
                            className="h-7 w-7 p-0 text-slate-400 hover:text-red-600"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Footer: pagination + batch delete */}
          <div className="flex items-center justify-between border-t border-slate-200 px-4 py-3">
            <div>
              {selectedIds.size > 0 && (
                <Button
                  variant="destructive"
                  size="sm"
                  onClick={() => setDeleteDialogOpen(true)}
                >
                  선택 삭제 ({selectedIds.size}개)
                </Button>
              )}
            </div>
            <div className="flex items-center gap-2 text-sm text-slate-600">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                이전
              </Button>
              <span>
                {page} / {totalPages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= totalPages}
                onClick={() => setPage((p) => p + 1)}
              >
                다음
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* Batch delete dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>파일 일괄 삭제</DialogTitle>
            <DialogDescription>
              선택한 {selectedIds.size}개 파일을 삭제하시겠습니까? 이 작업은
              되돌릴 수 없습니다.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={isDeleting}
            >
              취소
            </Button>
            <Button
              variant="destructive"
              onClick={handleBatchDelete}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <>
                  <Loader2 className="mr-1 h-4 w-4 animate-spin" />
                  삭제 중...
                </>
              ) : (
                "삭제"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </section>
  );
}
