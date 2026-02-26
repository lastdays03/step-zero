"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { AuditLog } from "./types";
import { fetchAuditLogs } from "./api";
import {
  Loader2, RefreshCw, Shield, Search, X, Download,
  ChevronLeft, ChevronRight, LayoutList, Clock,
  Filter, User, FileText, MessageSquare, ShieldBan,
  ShieldCheck, Eye, Trash2, RotateCcw, ChevronDown,
} from "lucide-react";

// ─── 액션 메타데이터 ──────────────────────────────────────────────────────────
const ACTION_META: Record<string, {
  label: string;
  color: "blue" | "green" | "orange" | "red" | "violet" | "slate";
  Icon: React.ElementType;
}> = {
  "growth_club.post.unblind": { label: "게시글 블라인드 해제", color: "green", Icon: RotateCcw },
  "growth_club.comment.unblind": { label: "댓글 블라인드 해제", color: "green", Icon: RotateCcw },
  "growth_club.post.delete": { label: "게시글 영구 삭제", color: "red", Icon: Trash2 },
  "growth_club.comment.delete": { label: "댓글 영구 삭제", color: "red", Icon: Trash2 },
  "ops.user.suspend": { label: "유저 정지", color: "orange", Icon: ShieldBan },
  "ops.user.unsuspend": { label: "유저 정지 해제", color: "blue", Icon: ShieldCheck },
  "growth_club.post.blind": { label: "게시글 블라인드", color: "orange", Icon: Eye },
  "growth_club.comment.blind": { label: "댓글 블라인드", color: "orange", Icon: Eye },
};

const COLOR_STYLES = {
  blue: "bg-blue-50   text-blue-700   border-blue-200",
  green: "bg-green-50  text-green-700  border-green-200",
  orange: "bg-orange-50 text-orange-700 border-orange-200",
  red: "bg-red-50    text-red-700    border-red-200",
  violet: "bg-violet-50 text-violet-700 border-violet-200",
  slate: "bg-slate-50  text-slate-600  border-slate-200",
};

const TARGET_TYPE_META: Record<string, { label: string; Icon: React.ElementType; color: string }> = {
  post: { label: "게시글", Icon: FileText, color: "text-indigo-500" },
  comment: { label: "댓글", Icon: MessageSquare, color: "text-violet-500" },
  user: { label: "유저", Icon: User, color: "text-orange-500" },
};

// ─── 유틸 ─────────────────────────────────────────────────────────────────────
function getActionMeta(action: string) {
  return ACTION_META[action] ?? {
    label: action,
    color: "slate" as const,
    Icon: Shield,
  };
}

function formatRelative(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diff = Math.floor((now - then) / 1000);
  if (diff < 60) return `${diff}초 전`;
  if (diff < 3600) return `${Math.floor(diff / 60)}분 전`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}시간 전`;
  return `${Math.floor(diff / 86400)}일 전`;
}

// ─── CSV 내보내기 ─────────────────────────────────────────────────────────────
function exportCsv(logs: AuditLog[]) {
  const headers = ["ID", "일시", "운영자", "액션", "대상타입", "대상ID", "대상자", "상세"];
  const rows = logs.map((l) => [
    l.id,
    new Date(l.created_at).toLocaleString("ko-KR"),
    l.actor_name,
    getActionMeta(l.action).label,
    l.target_type,
    l.target_id,
    l.target_author ?? "",
    (l.details ?? "").replace(/,/g, ""),
  ]);
  const csv = [headers, ...rows].map((r) => r.join(",")).join("\n");
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `audit-logs-${new Date().toISOString().split("T")[0]}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

// ─── 통계 카드 ────────────────────────────────────────────────────────────────
function StatCard({
  label, value, sub, color, Icon,
}: {
  label: string;
  value: number | string;
  sub?: string;
  color: "blue" | "green" | "red" | "orange";
  Icon: React.ElementType;
}) {
  const bg = { blue: "bg-blue-50 border-blue-100", green: "bg-green-50 border-green-100", red: "bg-red-50 border-red-100", orange: "bg-orange-50 border-orange-100" }[color];
  const ic = { blue: "text-blue-600", green: "text-green-600", red: "text-red-600", orange: "text-orange-600" }[color];
  const num = { blue: "text-blue-700", green: "text-green-700", red: "text-red-700", orange: "text-orange-700" }[color];
  return (
    <div className={`rounded-2xl border p-5 flex items-center gap-4 ${bg}`}>
      <div className="p-2.5 rounded-xl bg-white/70">
        <Icon className={`h-5 w-5 ${ic}`} />
      </div>
      <div>
        <p className="text-xs font-semibold text-slate-500 mb-0.5">{label}</p>
        <p className={`text-2xl font-black ${num}`}>{value}</p>
        {sub && <p className="text-[10px] text-slate-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── 액션 배지 ────────────────────────────────────────────────────────────────
function ActionBadge({ action }: { action: string }) {
  const meta = getActionMeta(action);
  const style = COLOR_STYLES[meta.color];
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${style}`}>
      <meta.Icon className="h-3 w-3" />
      {meta.label}
    </span>
  );
}

// ─── 타임라인 아이템 ──────────────────────────────────────────────────────────
function TimelineItem({ log, isLast }: { log: AuditLog; isLast: boolean }) {
  const meta = getActionMeta(log.action);
  const style = COLOR_STYLES[meta.color];
  const ttMeta = TARGET_TYPE_META[log.target_type] ?? { label: log.target_type, Icon: Shield, color: "text-slate-400" };

  return (
    <div className="flex gap-4">
      <div className="flex flex-col items-center">
        <div className={`w-8 h-8 rounded-full flex items-center justify-center ring-2 ring-white border ${style}`}>
          <meta.Icon className="h-4 w-4" />
        </div>
        {!isLast && <div className="w-px flex-1 bg-slate-100 mt-1 mb-1" />}
      </div>
      <div className={`pb-6 flex-1 ${isLast ? "" : ""}`}>
        <div className="flex items-start justify-between gap-2 mb-1.5">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-bold text-slate-800">{log.actor_name}</span>
            <span className="text-xs text-slate-400">이(가)</span>
            <ActionBadge action={log.action} />
            <span className="text-xs text-slate-400">조치함</span>
          </div>
          <span className="text-xs text-slate-400 whitespace-nowrap shrink-0" title={new Date(log.created_at).toLocaleString("ko-KR")}>
            {formatRelative(log.created_at)}
          </span>
        </div>
        <div className="flex items-center gap-3 text-xs text-slate-500">
          <span className={`flex items-center gap-1 ${ttMeta.color} font-semibold`}>
            <ttMeta.Icon className="h-3 w-3" />
            {ttMeta.label} #{log.target_id}
          </span>
          {log.target_author && (
            <>
              <span className="text-slate-300">·</span>
              <span className="flex items-center gap-1">
                <User className="h-3 w-3" />
                {log.target_author}
              </span>
            </>
          )}
          {log.details && (
            <>
              <span className="text-slate-300">·</span>
              <span className="text-slate-400 truncate max-w-xs">{log.details}</span>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── 메인 ────────────────────────────────────────────────────────────────────
const PAGE_SIZE = 20;

export function OpsAuditLogsView() {
  const { canRender } = useOpsAccessGuard();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [allLogs, setAllLogs] = useState<AuditLog[]>([]);  // 통계용 전체
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  // 필터 상태
  const [viewMode, setViewMode] = useState<"table" | "timeline">("table");
  const [searchQuery, setSearchQuery] = useState("");
  const [actionFilter, setActionFilter] = useState("all");
  const [targetTypeFilter, setTargetTypeFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  // 페이지네이션
  const [page, setPage] = useState(0);

  // ── 로드 ─────────────────────────────────────────────────────────────────
  const loadLogs = useCallback(async (quiet = false) => {
    try {
      if (!quiet) setIsLoading(true);
      else setIsRefreshing(true);

      // 전체 통계용 (필터 없이)
      const all = await fetchAuditLogs({ limit: 500 });
      setAllLogs(all);

      // 필터 적용하여 로드
      const filtered = await fetchAuditLogs({
        action: actionFilter !== "all" ? actionFilter : undefined,
        target_type: targetTypeFilter !== "all" ? targetTypeFilter : undefined,
        keyword: searchQuery || undefined,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        limit: 500,
      });
      setLogs(filtered);
      setPage(0);
    } catch (error) {
      console.error("Failed to fetch audit logs:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  }, [actionFilter, targetTypeFilter, searchQuery, dateFrom, dateTo]);

  useEffect(() => {
    if (canRender) void loadLogs();
  }, [canRender]);

  // ── 클라이언트 사이드 필터 (실시간 검색) ──────────────────────────────────
  const filteredLogs = useMemo(() => {
    return logs.filter((l) => {
      if (actionFilter !== "all" && l.action !== actionFilter) return false;
      if (targetTypeFilter !== "all" && l.target_type !== targetTypeFilter) return false;
      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        if (
          !l.actor_name.toLowerCase().includes(q) &&
          !l.action.toLowerCase().includes(q) &&
          !(l.target_author?.toLowerCase().includes(q)) &&
          !(l.details?.toLowerCase().includes(q)) &&
          !l.target_id.toLowerCase().includes(q)
        ) return false;
      }
      return true;
    });
  }, [logs, actionFilter, targetTypeFilter, searchQuery]);

  // ── 페이지네이션 ─────────────────────────────────────────────────────────
  const totalPages = Math.ceil(filteredLogs.length / PAGE_SIZE);
  const pagedLogs = filteredLogs.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);

  // ── 통계 ─────────────────────────────────────────────────────────────────
  const stats = useMemo(() => {
    const today = new Date().toDateString();
    return {
      total: allLogs.length,
      todayCount: allLogs.filter(l => new Date(l.created_at).toDateString() === today).length,
      deleteCount: allLogs.filter(l => l.action.includes("delete")).length,
      suspendCount: allLogs.filter(l => l.action.includes("suspend") && !l.action.includes("unsuspend")).length,
    };
  }, [allLogs]);

  // ── 액션 종류 목록 (동적) ─────────────────────────────────────────────────
  const uniqueActions = useMemo(() => {
    return Array.from(new Set(allLogs.map(l => l.action)));
  }, [allLogs]);

  const uniqueTargetTypes = useMemo(() => {
    return Array.from(new Set(allLogs.map(l => l.target_type)));
  }, [allLogs]);

  if (!canRender) return <OpsAccessPlaceholder />;

  const hasActiveFilter = actionFilter !== "all" || targetTypeFilter !== "all" || searchQuery || dateFrom || dateTo;

  return (
    <section className="space-y-6 pb-20 animate-in fade-in duration-500">

      {/* ── 통계 카드 ── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="전체 로그" value={stats.total} sub="모든 감사 기록" color="blue" Icon={Shield} />
        <StatCard label="오늘 조치" value={stats.todayCount} sub="24시간 이내" color="green" Icon={Clock} />
        <StatCard label="삭제 조치" value={stats.deleteCount} sub="영구 삭제 건" color="red" Icon={Trash2} />
        <StatCard label="유저 정지" value={stats.suspendCount} sub="누적 정지 건" color="orange" Icon={ShieldBan} />
      </div>

      {/* ── 메인 카드 ── */}
      <div className="bg-white rounded-3xl border border-slate-200 shadow-sm overflow-hidden">

        {/* 헤더 */}
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-blue-50 rounded-2xl">
                <Shield className="h-6 w-6 text-blue-600" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900">운영 감사로그</h1>
                <p className="text-sm text-slate-500">운영자가 수행한 모든 조치 이력을 투명하게 기록·추적합니다.</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {/* 뷰 전환 */}
              <div className="flex p-1 bg-slate-50 rounded-xl border border-slate-200 gap-1">
                <button
                  onClick={() => setViewMode("table")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${viewMode === "table" ? "bg-white shadow-sm text-slate-800 ring-1 ring-slate-200" : "text-slate-400 hover:text-slate-600"}`}
                >
                  <LayoutList className="h-3.5 w-3.5" />
                  테이블
                </button>
                <button
                  onClick={() => setViewMode("timeline")}
                  className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 ${viewMode === "timeline" ? "bg-white shadow-sm text-slate-800 ring-1 ring-slate-200" : "text-slate-400 hover:text-slate-600"}`}
                >
                  <Clock className="h-3.5 w-3.5" />
                  타임라인
                </button>
              </div>
              {/* CSV */}
              <button
                onClick={() => exportCsv(filteredLogs)}
                disabled={filteredLogs.length === 0}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-semibold border border-slate-200 transition-all disabled:opacity-40"
              >
                <Download className="h-3.5 w-3.5" />
                CSV 내보내기
              </button>
              {/* 새로고침 */}
              <button
                onClick={() => void loadLogs(true)}
                disabled={isRefreshing || isLoading}
                className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 text-xs font-semibold border border-slate-200 transition-all disabled:opacity-40"
              >
                <RefreshCw className={`h-3.5 w-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
                새로고침
              </button>
            </div>
          </div>

          {/* 필터 바 */}
          <div className="flex flex-wrap items-center gap-3">
            {/* 검색 */}
            <div className="relative flex-1 min-w-[200px]">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="운영자, 대상자, 상세내용 검색..."
                value={searchQuery}
                onChange={(e) => { setSearchQuery(e.target.value); setPage(0); }}
                className="w-full pl-10 pr-9 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-300 focus:border-blue-300 transition-all"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  <X className="h-4 w-4" />
                </button>
              )}
            </div>

            {/* 액션 필터 */}
            <div className="relative">
              <select
                value={actionFilter}
                onChange={(e) => { setActionFilter(e.target.value); setPage(0); }}
                className="appearance-none pl-4 pr-9 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 font-medium cursor-pointer"
              >
                <option value="all">전체 액션</option>
                {uniqueActions.map(a => (
                  <option key={a} value={a}>{getActionMeta(a).label}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            </div>

            {/* 대상 타입 필터 */}
            <div className="relative">
              <select
                value={targetTypeFilter}
                onChange={(e) => { setTargetTypeFilter(e.target.value); setPage(0); }}
                className="appearance-none pl-4 pr-9 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 font-medium cursor-pointer"
              >
                <option value="all">전체 타입</option>
                {uniqueTargetTypes.map(t => (
                  <option key={t} value={t}>{TARGET_TYPE_META[t]?.label ?? t}</option>
                ))}
              </select>
              <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400 pointer-events-none" />
            </div>

            {/* 날짜 범위 */}
            <div className="flex items-center gap-2">
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => { setDateFrom(e.target.value); setPage(0); }}
                className="px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 font-medium cursor-pointer"
              />
              <span className="text-slate-400 text-xs font-semibold">~</span>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => { setDateTo(e.target.value); setPage(0); }}
                className="px-3 py-2.5 rounded-xl border border-slate-200 bg-slate-50 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-300 font-medium cursor-pointer"
              />
            </div>

            {/* 필터 초기화 */}
            {hasActiveFilter && (
              <button
                onClick={() => {
                  setSearchQuery(""); setActionFilter("all");
                  setTargetTypeFilter("all"); setDateFrom(""); setDateTo(""); setPage(0);
                }}
                className="inline-flex items-center gap-1.5 px-3 py-2.5 rounded-xl bg-red-50 hover:bg-red-100 text-red-600 text-xs font-bold border border-red-200 transition-all"
              >
                <X className="h-3.5 w-3.5" />
                필터 초기화
              </button>
            )}
          </div>

          {/* 결과 수 */}
          {!isLoading && (
            <div className="mt-3 flex items-center gap-2">
              <Filter className="h-3.5 w-3.5 text-slate-400" />
              <span className="text-xs text-slate-500">
                <span className="font-bold text-slate-800">{filteredLogs.length}</span>건 표시 중
                {hasActiveFilter && <span className="text-slate-400"> (전체 {allLogs.length}건에서 필터됨)</span>}
              </span>
            </div>
          )}
        </div>

        {/* ── 컨텐츠 ── */}
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-24 gap-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <p className="text-sm text-slate-400 font-medium">감사로그를 불러오는 중...</p>
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-14 h-14 bg-slate-50 rounded-full flex items-center justify-center mb-4">
              <Shield className="text-slate-300" size={28} />
            </div>
            <h3 className="text-slate-700 font-bold">감사로그가 없습니다</h3>
            <p className="text-slate-400 text-sm mt-1">
              {hasActiveFilter ? "필터를 변경하거나 초기화해 보세요." : "운영 조치 내역이 발생하면 여기에 기록됩니다."}
            </p>
          </div>
        ) : viewMode === "table" ? (
          /* ── 테이블 뷰 ── */
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50/80 border-b border-slate-100">
                  <tr>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-40">일시</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-36">운영자</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-48">수행 작업</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-24 whitespace-nowrap">대상 타입</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-24">대상 ID</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500 w-36">대상자 계정</th>
                    <th className="px-6 py-4 text-xs font-bold text-slate-500">상세 내용</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-50">
                  {pagedLogs.map((log) => {
                    const ttMeta = TARGET_TYPE_META[log.target_type];
                    return (
                      <tr key={log.id} className="hover:bg-slate-50/40 transition-colors group">
                        <td className="px-6 py-4">
                          <div className="text-xs text-slate-600 font-mono">
                            {new Date(log.created_at).toLocaleString("ko-KR")}
                          </div>
                          <div className="text-[10px] text-slate-400 mt-0.5">
                            {formatRelative(log.created_at)}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <div className="w-7 h-7 rounded-full bg-blue-50 flex items-center justify-center text-blue-600 font-black text-xs flex-shrink-0">
                              {log.actor_name?.[0]?.toUpperCase() ?? "?"}
                            </div>
                            <span className="text-sm font-medium text-slate-700">{log.actor_name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <ActionBadge action={log.action} />
                        </td>
                        <td className="px-6 py-4">
                          {ttMeta ? (
                            <span className={`flex items-center gap-1 text-xs font-semibold whitespace-nowrap ${ttMeta.color}`}>
                              <ttMeta.Icon className="h-3.5 w-3.5" />
                              {ttMeta.label}
                            </span>
                          ) : (
                            <span className="text-xs text-slate-500 uppercase font-semibold tracking-wider">
                              {log.target_type}
                            </span>
                          )}
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-xs font-mono text-slate-500 bg-slate-100 px-2 py-0.5 rounded-lg">
                            #{log.target_id}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          {log.target_author ? (
                            <div className="flex items-center gap-1.5">
                              <User className="h-3.5 w-3.5 text-slate-400" />
                              <span className="text-sm font-medium text-slate-700">{log.target_author}</span>
                            </div>
                          ) : (
                            <span className="text-slate-300">—</span>
                          )}
                        </td>
                        <td className="px-6 py-4 text-xs text-slate-500 max-w-xs">
                          <span className="line-clamp-2">{log.details || "—"}</span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            {totalPages > 1 && (
              <div className="flex items-center justify-between px-6 py-4 border-t border-slate-100 bg-slate-50/50">
                <span className="text-xs text-slate-500">
                  {page * PAGE_SIZE + 1}–{Math.min((page + 1) * PAGE_SIZE, filteredLogs.length)} / {filteredLogs.length}건
                </span>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setPage(p => Math.max(0, p - 1))}
                    disabled={page === 0}
                    className="p-2 rounded-xl hover:bg-slate-100 disabled:opacity-30 transition-all text-slate-600"
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </button>
                  <div className="flex gap-1">
                    {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                      const pageIdx = totalPages <= 7 ? i : Math.max(0, Math.min(totalPages - 7, page - 3)) + i;
                      return (
                        <button
                          key={pageIdx}
                          onClick={() => setPage(pageIdx)}
                          className={`w-8 h-8 rounded-lg text-xs font-bold transition-all ${pageIdx === page
                            ? "bg-blue-600 text-white shadow-sm shadow-blue-200"
                            : "hover:bg-slate-100 text-slate-500"
                            }`}
                        >
                          {pageIdx + 1}
                        </button>
                      );
                    })}
                  </div>
                  <button
                    onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                    disabled={page >= totalPages - 1}
                    className="p-2 rounded-xl hover:bg-slate-100 disabled:opacity-30 transition-all text-slate-600"
                  >
                    <ChevronRight className="h-4 w-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        ) : (
          /* ── 타임라인 뷰 ── */
          <div className="p-8">
            {pagedLogs.map((log, idx) => (
              <TimelineItem key={log.id} log={log} isLast={idx === pagedLogs.length - 1} />
            ))}
            {totalPages > 1 && (
              <div className="flex items-center justify-center gap-3 mt-4 pt-4 border-t border-slate-100">
                <button
                  onClick={() => setPage(p => Math.max(0, p - 1))}
                  disabled={page === 0}
                  className="inline-flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 disabled:opacity-30 transition-all"
                >
                  <ChevronLeft className="h-4 w-4" />
                  이전
                </button>
                <span className="text-xs text-slate-400">{page + 1} / {totalPages}</span>
                <button
                  onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
                  disabled={page >= totalPages - 1}
                  className="inline-flex items-center gap-1 px-4 py-2 rounded-xl text-sm font-semibold text-slate-600 hover:bg-slate-100 disabled:opacity-30 transition-all"
                >
                  다음
                  <ChevronRight className="h-4 w-4" />
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </section>
  );
}
