"use client";

import React, { useEffect, useState, useCallback, Fragment } from "react";
import {
  Search,
  Filter,
  History,
  UserCog,
  AlertCircle,
  Loader2,
  Calendar,
  ChevronDown,
  ChevronUp
} from "lucide-react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";

import { fetchOpsUsers, updateUserStatus, bulkUpdateUserStatus } from "./api";
import type { OpsUser } from "./types";
import { DisciplineModal } from "./_components/DisciplineModal";
import { DisciplinaryHistoryList } from "./_components/DisciplinaryHistoryList";

export function OpsUsersView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();
  const [users, setUsers] = useState<OpsUser[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // States for filters
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");

  // UI States
  const [selectedUserIds, setSelectedUserIds] = useState<number[]>([]);
  const [expandedUserId, setExpandedUserId] = useState<number | null>(null);

  // Modal State
  const [selectedUser, setSelectedUser] = useState<OpsUser | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isBulkMode, setIsBulkMode] = useState(false);

  // Debounce search input (300ms)
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(search);
    }, 300);
    return () => clearTimeout(timer);
  }, [search]);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchOpsUsers({
        search: debouncedSearch || undefined,
        status: statusFilter || undefined
      });
      setUsers(data);
      setSelectedUserIds([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "사용자 정보를 불러오는 데 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [debouncedSearch, statusFilter]);

  useEffect(() => {
    if (canRender) {
      void load();
    }
  }, [canRender, load]);

  const handleUpdateStatus = async (status: string, reason: string, duration_days?: number) => {
    try {
      if (isBulkMode) {
        await bulkUpdateUserStatus({ user_ids: selectedUserIds, status, reason, duration_days });
      } else if (selectedUser) {
        await updateUserStatus(selectedUser.id, { status, reason, duration_days });
      }
      await load();
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const toggleSelectAll = () => {
    if (selectedUserIds.length === users.length) {
      setSelectedUserIds([]);
    } else {
      setSelectedUserIds((users || []).map(u => u.id));
    }
  };

  const toggleSelectUser = (id: number) => {
    setSelectedUserIds(prev =>
      prev.includes(id) ? prev.filter(i => i !== id) : [...prev, id]
    );
  };

  // Helper to convert UTC to KST
  const toKST = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const utcStr = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : `${dateStr.replace(' ', 'T')}Z`;
    const date = new Date(utcStr);

    const kstDate = new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).formatToParts(date);

    const find = (type: string) => kstDate.find(p => p.type === type)?.value || "";
    return `${find('year')}.${find('month')}.${find('day')} ${find('hour')}:${find('minute')}`;
  };

  const getStatusBadge = (user: OpsUser) => {
    const s = user.status;
    if (s === "active") return <Badge className="bg-green-100 text-green-700 hover:bg-green-200 border-none">정상</Badge>;
    if (s === "suspended") {
      let mainLabel = "정지(징계)";
      if (user.suspended_until) {
        const now = new Date();
        const target = user.suspended_until.includes('Z') || user.suspended_until.includes('+') ? user.suspended_until : `${user.suspended_until.replace(' ', 'T')}Z`;
        const until = new Date(target);
        const diffMs = until.getTime() - now.getTime();

        if (diffMs <= 0) {
          mainLabel = "해제 처리 중";
        } else if (diffMs < 24 * 60 * 60 * 1000) {
          const hours = Math.floor(diffMs / (1000 * 60 * 60));
          mainLabel = hours >= 1 ? `${hours}시간 남음` : "오늘 해제 예정";
        } else {
          const days = Math.ceil(diffMs / (1000 * 60 * 60 * 24));
          mainLabel = `징계 (${days}일 남음)`;
        }
      }
      return (
        <div className="flex flex-col gap-0.5">
          <Badge className="bg-amber-100 text-amber-700 hover:bg-amber-200 border-none w-fit font-bold">{mainLabel}</Badge>
          {user.suspended_until && (
            <span className="text-[9px] text-amber-600 font-bold whitespace-nowrap">
              만료: {toKST(user.suspended_until)} (KST)
            </span>
          )}
        </div>
      );
    }
    if (s === "suspended_permanent") return <Badge className="bg-red-100 text-red-700 hover:bg-red-200 border-none">영구 정지</Badge>;
    if (s === "suspended_inactive") return <Badge className="bg-slate-100 text-slate-700 hover:bg-slate-200 border-none">정지(휴면)</Badge>;
    return <Badge variant="secondary">{s}</Badge>;
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  return (
    <div className="space-y-6">
      {/* Header & Stats Search */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <UserCog className="text-blue-600" />
          사용자 관리
        </h1>
        <div className="flex items-center gap-4">
          {selectedUserIds.length > 0 && (
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 font-bold"
              onClick={() => {
                setIsBulkMode(true);
                setSelectedUser(null);
                setIsModalOpen(true);
              }}
            >
              일괄 조치 ({selectedUserIds.length})
            </Button>
          )}
          <div className="flex items-center gap-2">
            {isLoading && <Loader2 className="h-4 w-4 animate-spin text-slate-400" />}
            <span className="text-sm font-medium text-slate-500">총 {(users || []).length}명</span>
          </div>
        </div>
      </div>

      {/* Filters */}
      <Card className="border-slate-200 shadow-sm overflow-hidden">
        <CardContent className="p-4 bg-slate-50/50">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Status filter (left) */}
            <div className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-lg border border-slate-200 shadow-sm w-full md:w-auto">
              <Filter size={18} className="text-blue-600" />
              <span className="text-sm font-bold text-slate-700 whitespace-nowrap">상태 필터:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="h-9 px-2 rounded-md border-none bg-transparent text-sm font-semibold text-slate-900 outline-none cursor-pointer focus:ring-0 min-w-[140px]"
              >
                <option value="">모든 상태</option>
                <option value="active">정상 (Active)</option>
                <option value="suspended">기간 정지</option>
                <option value="suspended_permanent">영구 정지</option>
                <option value="suspended_inactive">30일 미접속</option>
              </select>
            </div>

            {/* Search bar (right) */}
            <div className="relative w-full md:w-64">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
              <input
                type="text"
                placeholder="이메일 또는 이름 검색..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full h-9 pl-9 pr-3 rounded-md border border-slate-200 bg-white text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-50 transition-all placeholder:text-slate-400"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* User Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden min-h-[400px]">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-3 w-10">
                  <Checkbox
                    checked={selectedUserIds.length === (users || []).length && (users || []).length > 0}
                    onCheckedChange={toggleSelectAll}
                  />
                </th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">사용자</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">상태 / 권한</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">활동 (KST)</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {isLoading && (users || []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-3" />
                    <p className="text-slate-500 italic">데이터를 불러오는 중입니다...</p>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-red-500">
                    <AlertCircle className="mx-auto mb-2" size={32} />
                    <p>{error}</p>
                  </td>
                </tr>
              ) : (users || []).length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-slate-400">
                    <div className="mx-auto h-12 w-12 rounded-full bg-slate-50 flex items-center justify-center mb-4">
                      <Search size={24} />
                    </div>
                    <p>검색 결과가 없습니다.</p>
                  </td>
                </tr>
              ) : (
                (users || []).map((user) => {
                  const isHighReport = user.report_count >= 15;
                  const isExpanded = expandedUserId === user.id;

                  return (
                    <Fragment key={user.id}>
                      <tr
                        className={`group transition-colors ${isHighReport ? 'bg-red-50/30' : 'hover:bg-slate-50/50'} ${selectedUserIds.includes(user.id) ? 'bg-blue-50/30' : ''}`}
                      >
                        <td className="px-6 py-4">
                          <Checkbox
                            checked={selectedUserIds.includes(user.id)}
                            onCheckedChange={() => toggleSelectUser(user.id)}
                          />
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col">
                            <span className={`text-sm font-bold ${isHighReport ? 'text-red-700' : 'text-slate-900'}`}>
                              {user.full_name || "이름 없음"}
                            </span>
                            <span className="text-xs text-slate-500">{user.email}</span>
                            <div className="flex items-center gap-2 mt-1">
                              <Calendar size={12} className="text-slate-400" />
                              <span className="text-[10px] text-slate-400 uppercase tracking-tighter font-medium">
                                Joined: {toKST(user.created_at)}
                              </span>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1.5 items-start">
                            {getStatusBadge(user)}
                            {user.is_superuser && (
                              <Badge variant="outline" className="text-[10px] py-0 border-slate-300 text-slate-600 font-bold uppercase">Admin</Badge>
                            )}
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex flex-col gap-1 text-[11px]">
                            {/* [BLIND] Growth Club Report Link - 팀 회의 결정에 따라 비활성화
                            <a
                              href={`/ops/reports?user_id=${user.id}`}
                              onClick={(e) => { e.preventDefault(); }}
                              className={`flex items-center gap-1 font-bold hover:underline cursor-pointer ${isHighReport ? 'text-red-600 bg-red-100/50 px-1.5 py-0.5 rounded w-fit' : 'text-blue-600'}`}
                            >
                              {isHighReport ? <AlertOctagon size={12} /> : <AlertCircle size={12} />}
                              {user.report_count}건 신고
                            </a>
                            */}
                            <div className="flex items-center gap-1 text-slate-400 font-medium whitespace-nowrap">
                              <History size={12} />
                              마지막 접속: {user.last_login_at ? toKST(user.last_login_at).split(' ').slice(-2).join(' ') : "-"}
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4 text-right">
                          <div className="flex items-center justify-end gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              className="text-slate-400 hover:text-slate-600"
                              onClick={() => setExpandedUserId(isExpanded ? null : user.id)}
                            >
                              {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </Button>
                            {!user.is_superuser && (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setIsBulkMode(false);
                                  setSelectedUser(user);
                                  setIsModalOpen(true);
                                }}
                                className={`${isHighReport ? 'border-red-200 text-red-600 hover:bg-red-50' : 'hover:bg-blue-50 hover:text-blue-600 hover:border-blue-200'} font-bold transition-all`}
                              >
                                조치하기
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                      {isExpanded && (
                        <tr className="bg-slate-50/30">
                          <td colSpan={5} className="px-12 py-4">
                            <div className="space-y-3">
                              <h4 className="text-xs font-bold text-slate-700 flex items-center gap-2">
                                <History size={14} /> 과거 징계 기록
                              </h4>
                              <DisciplinaryHistoryList userId={user.id} />
                            </div>
                          </td>
                        </tr>
                      )}
                    </Fragment>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <DisciplineModal
        user={isBulkMode ? null : selectedUser}
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setSelectedUser(null);
          setIsBulkMode(false);
        }}
        onConfirm={handleUpdateStatus}
        isBulk={isBulkMode}
        selectedCount={selectedUserIds.length}
      />
    </div>
  );
}
