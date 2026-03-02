"use client";

import { FileStack, Plus, RefreshCw } from "lucide-react";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";

import { deleteTemplate, fetchTemplates, fetchTemplateSummary } from "./api";
import { CreateFromRoadmapDialog } from "./components/create-from-roadmap-dialog";
import { TemplateListTable } from "./components/template-list-table";
import type { RoadmapTemplate, TemplateSummary, TemplateStatus } from "./types";

type TabKey = "all" | TemplateStatus;

const TABS: { key: TabKey; label: string }[] = [
  { key: "all", label: "전체" },
  { key: "DRAFT", label: "초안" },
  { key: "REVIEW", label: "검토중" },
  { key: "APPROVED", label: "승인" },
  { key: "ARCHIVED", label: "보관" },
];

const STAT_CARDS: {
  key: keyof TemplateSummary;
  label: string;
  color: string;
  bg: string;
}[] = [
  { key: "total", label: "전체", color: "text-slate-600", bg: "bg-slate-100" },
  { key: "draft", label: "초안", color: "text-slate-500", bg: "bg-slate-50" },
  {
    key: "review",
    label: "검토중",
    color: "text-amber-600",
    bg: "bg-amber-50",
  },
  {
    key: "approved",
    label: "승인",
    color: "text-emerald-600",
    bg: "bg-emerald-50",
  },
  {
    key: "archived",
    label: "보관",
    color: "text-gray-500",
    bg: "bg-gray-50",
  },
];

export function OpsRoadmapTemplatesView() {
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [templates, setTemplates] = useState<RoadmapTemplate[]>([]);
  const [summary, setSummary] = useState<TemplateSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabKey>("all");
  const [businessTypeFilter, setBusinessTypeFilter] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const [tmps, sum] = await Promise.all([
        fetchTemplates(),
        fetchTemplateSummary(),
      ]);
      setTemplates(tmps);
      setSummary(sum);
    } catch (err) {
      console.error("Failed to load templates:", err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (canRender) {
      void load();
    }
  }, [canRender, load]);

  const businessTypes = useMemo(() => {
    const types = new Set(templates.map((t) => t.business_type));
    return Array.from(types).sort();
  }, [templates]);

  const filtered = useMemo(() => {
    let result = templates;
    if (activeTab !== "all") {
      result = result.filter((t) => t.status === activeTab);
    }
    if (businessTypeFilter) {
      result = result.filter((t) => t.business_type === businessTypeFilter);
    }
    return result;
  }, [templates, activeTab, businessTypeFilter]);

  const handleDelete = async (template: RoadmapTemplate) => {
    if (
      !confirm(
        `"${template.title}" 템플릿을 삭제하시겠습니까?\n이 작업은 되돌릴 수 없습니다.`,
      )
    )
      return;
    try {
      await deleteTemplate(template.id);
      await load();
    } catch {
      alert("삭제에 실패했습니다.");
    }
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <h1 className="flex items-center gap-2 text-2xl font-bold text-slate-900">
          <FileStack className="text-blue-600" />
          로드맵 템플릿 관리
        </h1>
        <div className="flex gap-2">
          <Button
            size="sm"
            className="gap-2 bg-blue-600 hover:bg-blue-700"
            onClick={() => setIsCreateDialogOpen(true)}
          >
            <Plus size={14} />
            로드맵에서 생성
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => void load()}
            className="gap-2"
          >
            <RefreshCw size={14} />
            새로고침
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-5">
          {STAT_CARDS.map((stat) => (
            <Card key={stat.key} className="border-slate-200">
              <CardContent className="flex items-center gap-3 p-4">
                <div
                  className={`flex h-10 w-10 items-center justify-center rounded-xl ${stat.bg}`}
                >
                  <FileStack className={`h-5 w-5 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-2xl font-black text-slate-900">
                    {summary[stat.key]}
                  </p>
                  <p className="text-[10px] font-bold text-slate-400">
                    {stat.label}
                  </p>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1 flex-1 border-b border-slate-200">
          {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`relative px-4 py-2 text-sm font-bold transition-colors ${
              activeTab === tab.key
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
        {businessTypes.length > 1 && (
          <select
            value={businessTypeFilter}
            onChange={(e) => setBusinessTypeFilter(e.target.value)}
            className="h-9 rounded-md border border-slate-200 px-3 text-sm text-slate-700 outline-none focus:border-blue-500"
          >
            <option value="">전체 업종</option>
            {businessTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Table */}
      <TemplateListTable
        templates={filtered}
        isLoading={isLoading}
        onDelete={handleDelete}
      />

      {/* Footer */}
      <p className="text-xs text-slate-400">
        총 {filtered.length}개
        {activeTab !== "all" && ` (전체 ${templates.length}개 중)`}
      </p>

      {/* Dialogs */}
      <CreateFromRoadmapDialog
        isOpen={isCreateDialogOpen}
        onClose={() => setIsCreateDialogOpen(false)}
        onCreated={() => void load()}
      />
    </div>
  );
}
