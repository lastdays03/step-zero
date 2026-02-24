"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

import { fetchOpsAuditLogs } from "./api";
import type { OpsAuditLogItem } from "./types";

type FilterState = {
  actor: string;
  action: string;
  targetType: string;
  from: string;
  to: string;
  size: number;
};

const DEFAULT_FILTERS: FilterState = {
  actor: "",
  action: "",
  targetType: "",
  from: "",
  to: "",
  size: 20,
};

function toIsoDateTime(localDateTime: string): string {
  if (!localDateTime) return "";
  return new Date(localDateTime).toISOString();
}

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("ko-KR");
}

export function OpsAuditLogsView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [draftFilters, setDraftFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [appliedFilters, setAppliedFilters] = useState<FilterState>(DEFAULT_FILTERS);
  const [page, setPage] = useState(1);

  const [items, setItems] = useState<OpsAuditLogItem[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLog, setSelectedLog] = useState<OpsAuditLogItem | null>(null);

  useEffect(() => {
    if (!isAuthReady || !canRender) return;

    const load = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const result = await fetchOpsAuditLogs({
          actor: appliedFilters.actor ? Number(appliedFilters.actor) : undefined,
          action: appliedFilters.action || undefined,
          targetType: appliedFilters.targetType || undefined,
          from: appliedFilters.from ? toIsoDateTime(appliedFilters.from) : undefined,
          to: appliedFilters.to ? toIsoDateTime(appliedFilters.to) : undefined,
          page,
          size: appliedFilters.size,
        });

        setItems(result.items);
        setTotal(result.total);
        setSelectedLog((prev) => {
          if (!result.items.length) return null;
          if (!prev) return result.items[0];
          return result.items.find((item) => item.id === prev.id) ?? result.items[0];
        });
      } catch (err) {
        setError(err instanceof Error ? err.message : "감사로그 조회 중 오류가 발생했습니다.");
      } finally {
        setIsLoading(false);
      }
    };

    void load();
  }, [appliedFilters, canRender, isAuthReady, page]);

  const totalPages = useMemo(() => {
    if (total <= 0) return 1;
    return Math.ceil(total / appliedFilters.size);
  }, [appliedFilters.size, total]);

  const handleApplyFilters = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1);
    setAppliedFilters(draftFilters);
  };

  const handleResetFilters = () => {
    setDraftFilters(DEFAULT_FILTERS);
    setAppliedFilters(DEFAULT_FILTERS);
    setPage(1);
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <header>
        <h1 className="text-xl font-bold text-slate-900">운영 감사로그</h1>
        <p className="mt-2 text-sm text-slate-600">운영자 조치 이력을 필터 조회하고 상세 변경 내역을 확인합니다.</p>
      </header>

      <form onSubmit={handleApplyFilters} className="grid gap-3 rounded-xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-3">
        <label className="flex flex-col gap-1 text-xs text-slate-700">
          운영자 ID
          <input
            type="number"
            min={1}
            value={draftFilters.actor}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, actor: e.target.value }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="예: 1"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-700">
          액션 코드
          <input
            value={draftFilters.action}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, action: e.target.value }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="예: user.status.updated"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-700">
          대상 타입
          <input
            value={draftFilters.targetType}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, targetType: e.target.value }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            placeholder="예: announcement"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-700">
          시작 시각
          <input
            type="datetime-local"
            value={draftFilters.from}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, from: e.target.value }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-700">
          종료 시각
          <input
            type="datetime-local"
            value={draftFilters.to}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, to: e.target.value }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-700">
          페이지 크기
          <select
            value={draftFilters.size}
            onChange={(e) => setDraftFilters((prev) => ({ ...prev, size: Number(e.target.value) }))}
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
          >
            <option value={20}>20</option>
            <option value={50}>50</option>
            <option value={100}>100</option>
          </select>
        </label>

        <div className="col-span-full flex gap-2">
          <button type="submit" className="rounded-md bg-slate-900 px-3 py-2 text-sm font-semibold text-white">
            필터 적용
          </button>
          <button
            type="button"
            onClick={handleResetFilters}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold text-slate-700"
          >
            초기화
          </button>
        </div>
      </form>

      {isLoading ? <p className="text-sm text-slate-600">감사로그를 불러오는 중입니다...</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
      {!isLoading && !error && !items.length ? <p className="text-sm text-slate-600">조회 결과가 없습니다.</p> : null}

      {!isLoading && !error && items.length ? (
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="overflow-hidden rounded-xl border border-slate-200">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50 text-left text-xs text-slate-600">
                <tr>
                  <th className="px-3 py-2">시각</th>
                  <th className="px-3 py-2">운영자</th>
                  <th className="px-3 py-2">액션</th>
                  <th className="px-3 py-2">대상</th>
                  <th className="px-3 py-2">사유</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {items.map((item) => {
                  const isSelected = selectedLog?.id === item.id;
                  return (
                    <tr
                      key={item.id}
                      className={isSelected ? "bg-blue-50" : "hover:bg-slate-50"}
                      onClick={() => setSelectedLog(item)}
                    >
                      <td className="px-3 py-2">{formatDateTime(item.created_at)}</td>
                      <td className="px-3 py-2">#{item.admin_id}</td>
                      <td className="px-3 py-2 font-medium text-slate-900">{item.action}</td>
                      <td className="px-3 py-2">
                        {item.target_type}
                        {item.target_id ? `:${item.target_id}` : ""}
                      </td>
                      <td className="px-3 py-2 text-slate-600">{item.reason || "-"}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <div className="flex items-center justify-between border-t border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-600">
              <p>
                총 {total}건 | {page}/{totalPages} 페이지
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setPage((prev) => Math.max(1, prev - 1))}
                  disabled={page <= 1}
                  className="rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-50"
                >
                  이전
                </button>
                <button
                  type="button"
                  onClick={() => setPage((prev) => Math.min(totalPages, prev + 1))}
                  disabled={page >= totalPages}
                  className="rounded border border-slate-300 bg-white px-2 py-1 disabled:opacity-50"
                >
                  다음
                </button>
              </div>
            </div>
          </div>

          <aside className="rounded-xl border border-slate-200 bg-slate-50 p-4">
            <h2 className="text-sm font-bold text-slate-900">상세</h2>
            {!selectedLog ? (
              <p className="mt-2 text-sm text-slate-600">선택된 로그가 없습니다.</p>
            ) : (
              <div className="mt-2 space-y-2 text-xs text-slate-700">
                <p><span className="font-semibold">ID:</span> {selectedLog.id}</p>
                <p><span className="font-semibold">운영자:</span> #{selectedLog.admin_id}</p>
                <p><span className="font-semibold">액션:</span> {selectedLog.action}</p>
                <p><span className="font-semibold">대상:</span> {selectedLog.target_type}{selectedLog.target_id ? `:${selectedLog.target_id}` : ""}</p>
                <p><span className="font-semibold">사유:</span> {selectedLog.reason || "-"}</p>
                <p><span className="font-semibold">시각:</span> {formatDateTime(selectedLog.created_at)}</p>
                <div>
                  <p className="font-semibold">meta</p>
                  <pre className="mt-1 overflow-x-auto rounded bg-white p-2 text-[11px] text-slate-700">
                    {JSON.stringify(selectedLog.meta, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </aside>
        </div>
      ) : null}
    </section>
  );
}
