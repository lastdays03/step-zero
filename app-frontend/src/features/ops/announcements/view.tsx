"use client";

import React, { useEffect, useState, useCallback } from "react";
import {
  Plus,
  Search,
  MoreVertical,
  Loader2,
  Megaphone,
  Calendar,
  Eye,
  Edit2,
  Trash2,
  ChevronRight,
  Filter
} from "lucide-react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";

import { fetchOpsAnnouncements, createOpsAnnouncement, updateOpsAnnouncement, deleteOpsAnnouncement } from "./api";
import { OpsAnnouncement, OpsAnnouncementStatus } from "./types";
import { AnnouncementModal } from "./_components/AnnouncementModal";

export function OpsAnnouncementsView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [announcements, setAnnouncements] = useState<OpsAnnouncement[]>([]);
  const [total, setTotal] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // States for filters
  const [activeStatus, setActiveStatus] = useState<OpsAnnouncementStatus | undefined>(undefined);

  // UI States
  const [selectedAnnouncement, setSelectedAnnouncement] = useState<OpsAnnouncement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchOpsAnnouncements({
        status: activeStatus,
        limit: 50
      });
      setAnnouncements(data.items);
      setTotal(data.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "공지사항을 불러오는 데 실패했습니다.");
    } finally {
      setIsLoading(false);
    }
  }, [activeStatus]);

  useEffect(() => {
    if (canRender) {
      void load();
    }
  }, [canRender, load]);

  const handleSaveAnnouncement = async (data: { title: string; content: string; status: "draft" | "published" }) => {
    try {
      if (selectedAnnouncement) {
        await updateOpsAnnouncement(selectedAnnouncement.id, data);
      } else {
        await createOpsAnnouncement(data);
      }
      await load();
    } catch (err) {
      console.error(err);
      throw err;
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("정말로 이 공지사항을 삭제하시겠습니까?")) return;
    try {
      await deleteOpsAnnouncement(id);
      await load();
    } catch (err) {
      alert("삭제에 실패했습니다: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const handleStatusToggle = async (announcement: OpsAnnouncement) => {
    const newStatus: OpsAnnouncementStatus = announcement.status === "published" ? "archived" : "published";
    const msg = newStatus === "published" ? "이 공지를 게시하시겠습니까?" : "이 공지를 내리시겠습니까?";
    if (!confirm(msg)) return;

    try {
      await updateOpsAnnouncement(announcement.id, { status: newStatus });
      await load();
    } catch (err) {
      alert("상태 변경에 실패했습니다: " + (err instanceof Error ? err.message : String(err)));
    }
  };

  const toKST = (dateStr: string | null) => {
    if (!dateStr) return "-";
    const utcStr = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : `${dateStr.replace(' ', 'T')}Z`;
    const date = new Date(utcStr);

    return new Intl.DateTimeFormat("ko-KR", {
      timeZone: "Asia/Seoul",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }).format(date).replace(/\. /g, '.').replace(':', ':');
  };

  const getStatusBadge = (status: OpsAnnouncementStatus) => {
    const config = {
      draft: { label: "초안", className: "bg-slate-100 text-slate-600 border-none" },
      published: { label: "게시 중", className: "bg-green-100 text-green-700 border-none" },
      archived: { label: "내림", className: "bg-amber-100 text-amber-700 border-none" }
    };
    const { label, className } = config[status];
    return <Badge className={className}>{label}</Badge>;
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 flex items-center gap-2">
          <Megaphone className="text-blue-600" />
          공지 관리
        </h1>
        <Button
          onClick={() => {
            setSelectedAnnouncement(null);
            setIsModalOpen(true);
          }}
          className="bg-blue-600 hover:bg-blue-700 font-bold gap-2"
        >
          <Plus size={18} />
          새 공지 작성
        </Button>
      </div>

      {/* Status Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200">
        <button
          onClick={() => setActiveStatus(undefined)}
          className={`px-4 py-2 text-sm font-bold transition-colors relative ${!activeStatus ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          전체
          {!activeStatus && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />}
        </button>
        <button
          onClick={() => setActiveStatus("draft")}
          className={`px-4 py-2 text-sm font-bold transition-colors relative ${activeStatus === "draft" ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          초안
          {activeStatus === "draft" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />}
        </button>
        <button
          onClick={() => setActiveStatus("published")}
          className={`px-4 py-2 text-sm font-bold transition-colors relative ${activeStatus === "published" ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          게시
          {activeStatus === "published" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />}
        </button>
        <button
          onClick={() => setActiveStatus("archived")}
          className={`px-4 py-2 text-sm font-bold transition-colors relative ${activeStatus === "archived" ? 'text-blue-600' : 'text-slate-500 hover:text-slate-700'}`}
        >
          내림
          {activeStatus === "archived" && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />}
        </button>
      </div>

      {/* List Table */}
      <Card className="border-slate-200 shadow-sm overflow-hidden min-h-[400px]">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200">
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">제목</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">상태</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">작성일 (KST)</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider">게시일 (KST)</th>
                <th className="px-6 py-3 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">관리</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <Loader2 className="h-8 w-8 animate-spin text-blue-600 mx-auto mb-3" />
                    <p className="text-slate-500 italic">공지사항을 불러오는 중입니다...</p>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-red-500 p-6">
                    <p>{error}</p>
                    <Button variant="outline" size="sm" onClick={() => void load()} className="mt-4">다시 시도</Button>
                  </td>
                </tr>
              ) : announcements.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center text-slate-400">
                    <Megaphone size={32} className="mx-auto mb-3 opacity-20" />
                    <p>등록된 공지사항이 없습니다.</p>
                  </td>
                </tr>
              ) : (
                announcements.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50/50 transition-colors group">
                    <td className="px-6 py-4">
                      <div className="flex flex-col max-w-md">
                        <span className="text-sm font-bold text-slate-900 line-clamp-1">{item.title}</span>
                        <span className="text-[11px] text-slate-400 mt-0.5 line-clamp-1">{item.content.substring(0, 60)}...</span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      {getStatusBadge(item.status)}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">
                      {toKST(item.created_at)}
                    </td>
                    <td className="px-6 py-4 text-xs text-slate-500 whitespace-nowrap">
                      {item.published_at ? toKST(item.published_at) : "-"}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAnnouncement(item);
                            setIsModalOpen(true);
                          }}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-blue-600"
                        >
                          <Edit2 size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleDelete(item.id)}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-red-600"
                        >
                          <Trash2 size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleStatusToggle(item)}
                          className={`h-8 w-8 p-0 transition-colors ${item.status === 'published' ? 'text-amber-500 hover:text-amber-600' : 'text-green-500 hover:text-green-600'}`}
                          title={item.status === 'published' ? '게시 중단' : '게시하기'}
                        >
                          <ChevronRight size={14} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Footer Info */}
      <div className="flex items-center justify-between px-2">
        <p className="text-xs text-slate-400 font-medium">
          총 {total}개의 공지사항이 검색되었습니다.
        </p>
      </div>

      <AnnouncementModal
        announcement={selectedAnnouncement}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleSaveAnnouncement}
      />
    </div>
  );
}
