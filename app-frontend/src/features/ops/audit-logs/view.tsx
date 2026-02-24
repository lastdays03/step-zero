"use client";

import React, { useEffect, useState } from "react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { AuditLog } from "./types";
import { fetchAuditLogs } from "./api";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Loader2, RefreshCw, User, Shield, Info } from "lucide-react";

export function OpsAuditLogsView() {
  const { canRender } = useOpsAccessGuard();
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const loadLogs = async (quiet = false) => {
    try {
      if (!quiet) setIsLoading(true);
      else setIsRefreshing(true);
      const data = await fetchAuditLogs();
      setLogs(data);
    } catch (error) {
      console.error("Failed to fetch audit logs:", error);
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    if (canRender) {
      loadLogs();
    }
  }, [canRender]);

  if (!canRender) return <OpsAccessPlaceholder />;

  const formatAction = (action: string) => {
    const actionMap: Record<string, string> = {
      "growth_club.post.unblind": "게시글 블라인드 해제",
      "growth_club.comment.unblind": "댓글 블라인드 해제",
    };
    return actionMap[action] || action;
  };

  return (
    <section className="space-y-6">
      <header className="flex items-center justify-between bg-white p-6 rounded-2xl border border-zinc-100 shadow-sm">
        <div>
          <h1 className="text-xl font-bold text-zinc-900 flex items-center gap-2">
            <Shield className="text-blue-600" size={24} />
            운영 감사로그
          </h1>
          <p className="mt-1 text-sm text-zinc-500">운영자가 수행한 모든 조치 이력을 투명하게 기록하고 추적합니다.</p>
        </div>
        <button
          onClick={() => loadLogs(true)}
          disabled={isRefreshing || isLoading}
          className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-zinc-600 bg-zinc-50 hover:bg-zinc-100 rounded-xl transition-all disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${isRefreshing ? "animate-spin" : ""}`} />
          새로고침
        </button>
      </header>

      <div className="bg-white rounded-2xl border border-zinc-100 shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
            <p className="text-sm text-zinc-500 font-medium">감사로그를 불러오는 중...</p>
          </div>
        ) : logs.length > 0 ? (
          <Table>
            <TableHeader className="bg-zinc-50">
              <TableRow>
                <TableHead className="w-[180px]">일시</TableHead>
                <TableHead className="w-[120px]">운영자</TableHead>
                <TableHead className="w-[180px]">수행 작업</TableHead>
                <TableHead className="w-[100px]">대상 타입</TableHead>
                <TableHead>상세 내용</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.map((log) => (
                <TableRow key={log.id} className="hover:bg-zinc-50 transition-colors">
                  <TableCell className="text-xs text-zinc-500 font-mono">
                    {new Date(log.created_at).toLocaleString("ko-KR")}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-blue-50 flex items-center justify-center">
                        <User size={12} className="text-blue-600" />
                      </div>
                      <span className="text-sm font-medium text-zinc-700">{log.actor_name}</span>
                    </div>
                  </TableCell>
                  <TableCell>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-100">
                      {formatAction(log.action)}
                    </span>
                  </TableCell>
                  <TableCell>
                    <span className="text-xs text-zinc-500 uppercase font-semibold tracking-wider">
                      {log.target_type}
                    </span>
                  </TableCell>
                  <TableCell className="text-sm text-zinc-600">
                    <div className="flex items-start gap-2">
                      <Info size={14} className="mt-1 text-zinc-400 shrink-0" />
                      <span>{log.details || "-"}</span>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        ) : (
          <div className="flex flex-col items-center justify-center py-20 text-center">
            <div className="w-12 h-12 bg-zinc-50 rounded-full flex items-center justify-center mb-4">
              <Shield className="text-zinc-300" size={24} />
            </div>
            <h3 className="text-zinc-900 font-semibold">감사로그가 없습니다</h3>
            <p className="text-zinc-500 text-sm mt-1">운영 조치 내역이 발생하면 여기에 기록됩니다.</p>
          </div>
        )}
      </div>
    </section>
  );
}
