"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import {
  Plus,
  Loader2,
  Megaphone,
  Edit2,
  ChevronRight,
} from "lucide-react";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

import {
  fetchOpsAnnouncements,
  createOpsAnnouncement,
  updateOpsAnnouncement,
  updateOpsAnnouncementStatus,
} from "./api";
import type { OpsAnnouncement, OpsAnnouncementStatus } from "./types";
import { AnnouncementModal } from "./_components/AnnouncementModal";

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function toKST(dateStr: string | null): string {
  if (!dateStr) return "-";
  const utcStr =
    dateStr.includes("Z") || dateStr.includes("+")
      ? dateStr
      : `${dateStr.replace(" ", "T")}Z`;
  const date = new Date(utcStr);

  return new Intl.DateTimeFormat("ko-KR", {
    timeZone: "Asia/Seoul",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  })
    .format(date)
    .replace(/\. /g, ".")
    .replace(":", ":");
}

const STATUS_CONFIG: Record<
  OpsAnnouncementStatus,
  { label: string; className: string }
> = {
  draft: { label: "초안", className: "bg-slate-100 text-slate-600 border-none" },
  published: {
    label: "게시 중",
    className: "bg-green-100 text-green-700 border-none",
  },
  archived: {
    label: "내림",
    className: "bg-amber-100 text-amber-700 border-none",
  },
};

function StatusBadge({ status }: { status: OpsAnnouncementStatus }) {
  const { label, className } = STATUS_CONFIG[status];
  return <Badge className={className}>{label}</Badge>;
}

/* ------------------------------------------------------------------ */
/*  Tab definitions                                                    */
/* ------------------------------------------------------------------ */

type TabKey = "all" | OpsAnnouncementStatus;

const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "draft", label: "초안" },
  { key: "published", label: "게시" },
  { key: "archived", label: "내림" },
];

/* ------------------------------------------------------------------ */
/*  Main view                                                          */
/* ------------------------------------------------------------------ */

export function OpsAnnouncementsView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [announcements, setAnnouncements] = useState<OpsAnnouncement[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // filter
  const [activeTab, setActiveTab] = useState<TabKey>("all");

  // modal
  const [selectedAnnouncement, setSelectedAnnouncement] =
    useState<OpsAnnouncement | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  /* ---- data fetching ---- */

  const load = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchOpsAnnouncements();
      setAnnouncements(data.items);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "공지사항을 불러오는 데 실패했습니다.",
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canRender) {
      void load();
    }
  }, [canRender, load]);

  /* ---- client-side filtering ---- */

  const filteredAnnouncements = useMemo(() => {
    if (activeTab === "all") return announcements;
    return announcements.filter((a) => a.status === activeTab);
  }, [announcements, activeTab]);

  /* ---- handlers ---- */

  const handleSaveAnnouncement = async (data: {
    title: string;
    content: string;
    publish: boolean;
  }) => {
    if (selectedAnnouncement) {
      // update title/content
      await updateOpsAnnouncement(selectedAnnouncement.id, {
        title: data.title,
        content: data.content,
      });
      // if publish flag changed, update status
      if (data.publish && selectedAnnouncement.status !== "published") {
        await updateOpsAnnouncementStatus(selectedAnnouncement.id, {
          status: "published",
        });
      }
    } else {
      // create new announcement (always created as draft)
      const created = await createOpsAnnouncement({
        title: data.title,
        content: data.content,
      });
      // if user chose to publish immediately
      if (data.publish) {
        await updateOpsAnnouncementStatus(created.id, { status: "published" });
      }
    }
    await load();
  };

  const handleStatusToggle = async (announcement: OpsAnnouncement) => {
    const newStatus: OpsAnnouncementStatus =
      announcement.status === "published" ? "archived" : "published";
    const msg =
      newStatus === "published"
        ? "이 공지를 게시하시겠습니까?"
        : "이 공지를 내리시겠습니까?";
    if (!confirm(msg)) return;

    try {
      await updateOpsAnnouncementStatus(announcement.id, { status: newStatus });
      await load();
    } catch (err) {
      toast.error(
        "상태 변경에 실패했습니다: " +
        (err instanceof Error ? err.message : String(err)),
      );
    }
  };

  /* ---- guard ---- */

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  /* ---- render ---- */

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold tracking-tight text-slate-900">
          <Megaphone className="text-blue-600" />
          공지 관리
        </h1>
        <Button
          onClick={() => {
            setSelectedAnnouncement(null);
            setIsModalOpen(true);
          }}
          className="gap-2 bg-blue-600 font-bold hover:bg-blue-700"
        >
          <Plus size={18} />
          새 공지 작성
        </Button>
      </div>

      {/* Status Tabs */}
      <div className="flex items-center gap-1 border-b border-slate-200">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`relative px-4 py-2 text-sm font-bold transition-colors ${activeTab === tab.key
                ? "text-blue-600"
                : "text-slate-500 hover:text-slate-700"
              }`}
          >
            {tab.label}
            {activeTab === tab.key && (
              <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
            )}
          </button>
        ))}
      </div>

      {/* List Table */}
      <Card className="min-h-[400px] overflow-hidden border-slate-200 shadow-sm">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                  제목
                </th>
                <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                  상태
                </th>
                <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                  작성일 (KST)
                </th>
                <th className="px-6 py-3 text-xs font-bold uppercase tracking-wider text-slate-500">
                  수정일 (KST)
                </th>
                <th className="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-500">
                  관리
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {isLoading ? (
                <tr>
                  <td colSpan={5} className="py-20 text-center">
                    <Loader2 className="mx-auto mb-3 h-8 w-8 animate-spin text-blue-600" />
                    <p className="italic text-slate-500">
                      공지사항을 불러오는 중입니다...
                    </p>
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td
                    colSpan={5}
                    className="p-6 py-20 text-center text-red-500"
                  >
                    <p>{error}</p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => void load()}
                      className="mt-4"
                    >
                      다시 시도
                    </Button>
                  </td>
                </tr>
              ) : filteredAnnouncements.length === 0 ? (
                <tr>
                  <td
                    colSpan={5}
                    className="py-20 text-center text-slate-400"
                  >
                    <Megaphone size={32} className="mx-auto mb-3 opacity-20" />
                    <p>등록된 공지사항이 없습니다.</p>
                  </td>
                </tr>
              ) : (
                filteredAnnouncements.map((item) => (
                  <tr
                    key={item.id}
                    className="group transition-colors hover:bg-slate-50/50"
                  >
                    <td className="px-6 py-4">
                      <div className="flex max-w-md flex-col">
                        <span className="line-clamp-1 text-sm font-bold text-slate-900">
                          {item.title}
                        </span>
                        <span className="mt-0.5 line-clamp-1 text-[11px] text-slate-400">
                          {item.content.substring(0, 60)}
                          {item.content.length > 60 ? "..." : ""}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">
                      {toKST(item.created_at)}
                    </td>
                    <td className="whitespace-nowrap px-6 py-4 text-xs text-slate-500">
                      {toKST(item.updated_at)}
                    </td>
                    <td className="px-6 py-4 text-right">
                      <div className="flex items-center justify-end gap-1 opacity-0 transition-opacity group-hover:opacity-100">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setSelectedAnnouncement(item);
                            setIsModalOpen(true);
                          }}
                          className="h-8 w-8 p-0 text-slate-400 hover:text-blue-600"
                          title="수정"
                        >
                          <Edit2 size={14} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleStatusToggle(item)}
                          className={`h-8 w-8 p-0 transition-colors ${item.status === "published"
                              ? "text-amber-500 hover:text-amber-600"
                              : "text-green-500 hover:text-green-600"
                            }`}
                          title={
                            item.status === "published"
                              ? "게시 중단"
                              : "게시하기"
                          }
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
        <p className="text-xs font-medium text-slate-400">
          총 {filteredAnnouncements.length}개의 공지사항
          {activeTab !== "all" &&
            ` (전체 ${announcements.length}개 중)`}
        </p>
      </div>

      {/* Create/Edit Modal */}
      <AnnouncementModal
        announcement={selectedAnnouncement}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleSaveAnnouncement}
      />
    </div>
  );
}
