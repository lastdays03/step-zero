"use client";

import { Eye, Trash2 } from "lucide-react";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";

import type { RoadmapTemplate } from "../types";
import { TemplateStatusBadge } from "./template-status-badge";

function formatDate(iso: string) {
  return new Date(iso).toLocaleDateString("ko-KR", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  });
}

interface TemplateListTableProps {
  templates: RoadmapTemplate[];
  isLoading: boolean;
  onDelete: (template: RoadmapTemplate) => void;
}

export function TemplateListTable({
  templates,
  isLoading,
  onDelete,
}: TemplateListTableProps) {
  const router = useRouter();

  return (
    <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
      <table className="w-full">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50">
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              업종
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              창업방식
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              창업형태
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              제목
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              상태
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              버전
            </th>
            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-slate-500">
              생성일
            </th>
            <th className="px-6 py-3 text-right text-xs font-bold uppercase tracking-wider text-slate-500">
              관리
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100">
          {isLoading ? (
            <tr>
              <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                로딩 중...
              </td>
            </tr>
          ) : templates.length === 0 ? (
            <tr>
              <td colSpan={8} className="px-6 py-12 text-center text-slate-400">
                등록된 템플릿이 없습니다.
              </td>
            </tr>
          ) : (
            templates.map((t) => (
              <tr
                key={t.id}
                className="cursor-pointer transition-colors hover:bg-slate-50"
                onClick={() =>
                  router.push(`/ops/roadmap-templates/${t.id}`)
                }
              >
                <td className="px-6 py-4 text-sm font-medium text-slate-900">
                  {t.business_type}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {t.startup_method || "-"}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {t.startup_type || "-"}
                </td>
                <td className="px-6 py-4 text-sm text-slate-700">
                  {t.title}
                </td>
                <td className="px-6 py-4">
                  <TemplateStatusBadge status={t.status} />
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  v{t.version}
                </td>
                <td className="px-6 py-4 text-sm text-slate-500">
                  {formatDate(t.created_at)}
                </td>
                <td className="px-6 py-4 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        router.push(`/ops/roadmap-templates/${t.id}`);
                      }}
                    >
                      <Eye size={14} />
                    </Button>
                    {(t.status === "DRAFT" || t.status === "REVIEW") && (
                      <Button
                        variant="ghost"
                        size="sm"
                        className="text-red-500 hover:text-red-700"
                        onClick={(e) => {
                          e.stopPropagation();
                          onDelete(t);
                        }}
                      >
                        <Trash2 size={14} />
                      </Button>
                    )}
                  </div>
                </td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
}
