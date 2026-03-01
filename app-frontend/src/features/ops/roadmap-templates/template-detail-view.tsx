"use client";

import {
  ArrowLeft,
  CheckCircle,
  Clock,
  FileText,
  Save,
} from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";

import {
  fetchTemplateDetail,
  updateTemplate,
  updateTemplateStatus,
} from "./api";
import { TemplateStatusBadge } from "./components/template-status-badge";
import { TemplateStepEditor } from "./components/template-step-editor";
import type { RoadmapTemplateDetail, TemplateStatus } from "./types";

const NEXT_STATUS: Partial<Record<TemplateStatus, { label: string; value: TemplateStatus }>> = {
  DRAFT: { label: "검토 요청", value: "REVIEW" },
  REVIEW: { label: "승인", value: "APPROVED" },
  APPROVED: { label: "보관 처리", value: "ARCHIVED" },
};

const REJECT_STATUS: Partial<Record<TemplateStatus, { label: string; value: TemplateStatus }>> = {
  REVIEW: { label: "반려 (초안으로)", value: "DRAFT" },
};

interface TemplateDetailViewProps {
  templateId: number;
}

export function TemplateDetailView({ templateId }: TemplateDetailViewProps) {
  const router = useRouter();
  const { canRender, isAuthReady } = useOpsAccessGuard();

  const [template, setTemplate] = useState<RoadmapTemplateDetail | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [editTitle, setEditTitle] = useState("");
  const [editBusinessType, setEditBusinessType] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchTemplateDetail(templateId);
      setTemplate(data);
      setEditTitle(data.title);
      setEditBusinessType(data.business_type);
    } catch {
      console.error("Failed to load template detail");
    } finally {
      setIsLoading(false);
    }
  }, [templateId]);

  useEffect(() => {
    if (canRender) {
      void load();
    }
  }, [canRender, load]);

  const editable =
    template?.status === "DRAFT" || template?.status === "REVIEW";

  const handleSaveMeta = async () => {
    if (!template) return;
    setIsSaving(true);
    try {
      await updateTemplate(template.id, {
        title: editTitle,
        business_type: editBusinessType,
      });
      await load();
    } catch {
      alert("저장에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleStatusChange = async (newStatus: TemplateStatus) => {
    if (!template) return;
    const reason = prompt("사유를 입력하세요 (선택):");
    try {
      await updateTemplateStatus(template.id, {
        new_status: newStatus,
        reason: reason || undefined,
      });
      await load();
    } catch (err) {
      alert(
        "상태 변경 실패: " +
          (err instanceof Error ? err.message : String(err)),
      );
    }
  };

  if (!isAuthReady || !canRender) return <OpsAccessPlaceholder />;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        로딩 중...
      </div>
    );
  }

  if (!template) {
    return (
      <div className="flex items-center justify-center py-20 text-slate-400">
        템플릿을 찾을 수 없습니다.
      </div>
    );
  }

  const nextAction = NEXT_STATUS[template.status];
  const rejectAction = REJECT_STATUS[template.status];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push("/ops/roadmap-templates")}
        >
          <ArrowLeft size={16} />
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-slate-900">
              {template.title}
            </h1>
            <TemplateStatusBadge status={template.status} />
            <span className="text-sm text-slate-400">v{template.version}</span>
          </div>
          <p className="mt-1 text-sm text-slate-500">
            업종: {template.business_type}
            {template.startup_method && ` / ${template.startup_method}`}
          </p>
        </div>

        {/* Status actions */}
        <div className="flex gap-2">
          {rejectAction && (
            <Button
              variant="outline"
              size="sm"
              className="text-red-600"
              onClick={() => handleStatusChange(rejectAction.value)}
            >
              {rejectAction.label}
            </Button>
          )}
          {nextAction && (
            <Button
              size="sm"
              className="gap-2 bg-blue-600 hover:bg-blue-700"
              onClick={() => handleStatusChange(nextAction.value)}
            >
              <CheckCircle size={14} />
              {nextAction.label}
            </Button>
          )}
        </div>
      </div>

      {/* Meta edit */}
      {editable && (
        <Card>
          <CardContent className="space-y-4 p-4">
            <h2 className="flex items-center gap-2 text-sm font-bold text-slate-700">
              <FileText size={14} /> 기본 정보 수정
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500">
                  제목
                </label>
                <input
                  type="text"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500">
                  업종
                </label>
                <input
                  type="text"
                  value={editBusinessType}
                  onChange={(e) => setEditBusinessType(e.target.value)}
                  className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500"
                />
              </div>
            </div>
            <Button
              size="sm"
              onClick={handleSaveMeta}
              disabled={isSaving}
              className="gap-2"
            >
              <Save size={14} />
              {isSaving ? "저장 중..." : "저장"}
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Info cards */}
      <div className="grid grid-cols-3 gap-3">
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <Clock className="h-5 w-5 text-blue-500" />
            <div>
              <p className="text-lg font-bold">
                {template.steps.reduce(
                  (sum, s) => sum + s.estimated_days,
                  0,
                )}
                일
              </p>
              <p className="text-xs text-slate-400">예상 소요일</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <FileText className="h-5 w-5 text-emerald-500" />
            <div>
              <p className="text-lg font-bold">{template.steps.length}개</p>
              <p className="text-xs text-slate-400">단계</p>
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex items-center gap-3 p-4">
            <CheckCircle className="h-5 w-5 text-amber-500" />
            <div>
              <p className="text-lg font-bold">
                {template.steps.reduce(
                  (sum, s) => sum + s.actions.length,
                  0,
                )}
                개
              </p>
              <p className="text-xs text-slate-400">총 액션</p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Steps */}
      <div className="space-y-3">
        <h2 className="text-lg font-bold text-slate-900">
          단계 ({template.steps.length})
        </h2>
        {template.steps.map((step) => (
          <TemplateStepEditor
            key={step.id}
            step={step}
            templateId={template.id}
            editable={editable}
            onActionChange={load}
          />
        ))}
      </div>
    </div>
  );
}
