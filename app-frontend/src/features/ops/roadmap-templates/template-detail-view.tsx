"use client";

import {
  AlertCircle,
  ArrowLeft,
  BookOpen,
  CheckCircle,
  Clock,
  Database,
  FileText,
  Plus,
  Save,
  Sparkles,
} from "lucide-react";
import { useRouter } from "next/navigation";
import React, { useCallback, useEffect, useState } from "react";
import {
  DragDropContext,
  Draggable,
  Droppable,
  type DropResult,
} from "@hello-pangea/dnd";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";
import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";

import {
  createTemplateStep,
  fetchTemplateDetail,
  reorderTemplateSteps,
  updateTemplate,
  updateTemplateStatus,
} from "./api";
import { StatusChangeDialog } from "./components/status-change-dialog";
import { TemplateStatusBadge } from "./components/template-status-badge";
import { TemplateStepEditor } from "./components/template-step-editor";
import type { RoadmapTemplateDetail, TemplateStatus } from "./types";

const MAPPING_SOURCE_DISPLAY: Record<string, { label: string; className: string; icon: typeof BookOpen }> = {
  actionkit_direct: {
    label: "법령 기반",
    className: "bg-emerald-50 text-emerald-700 border-emerald-200",
    icon: BookOpen,
  },
  rag: {
    label: "AI 분석",
    className: "bg-blue-50 text-blue-700 border-blue-200",
    icon: Database,
  },
  fallback: {
    label: "일반 안내",
    className: "bg-amber-50 text-amber-700 border-amber-200",
    icon: AlertCircle,
  },
  llm_generated: {
    label: "AI 생성",
    className: "bg-purple-50 text-purple-700 border-purple-200",
    icon: Sparkles,
  },
  template: {
    label: "템플릿",
    className: "bg-indigo-50 text-indigo-700 border-indigo-200",
    icon: BookOpen,
  },
};

function computeMappingSourceDistribution(template: RoadmapTemplateDetail) {
  const counts: Record<string, number> = {};
  let total = 0;
  for (const step of template.steps) {
    for (const action of step.actions) {
      const src = action.metadata_json?.mapping_source as string | undefined;
      if (src) {
        counts[src] = (counts[src] || 0) + 1;
        total++;
      }
    }
  }
  return { counts, total };
}

const NEXT_STATUS: Partial<Record<TemplateStatus, { label: string; value: TemplateStatus }>> = {
  DRAFT: { label: "검토 요청", value: "REVIEW" },
  REVIEW: { label: "승인", value: "APPROVED" },
  APPROVED: { label: "보관 처리", value: "ARCHIVED" },
};

const REJECT_STATUS: Partial<Record<TemplateStatus, { label: string; value: TemplateStatus }>> = {
  REVIEW: { label: "반려 (초안으로)", value: "DRAFT" },
  APPROVED: { label: "검토로 되돌리기", value: "REVIEW" },
  ARCHIVED: { label: "승인으로 복원", value: "APPROVED" },
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
  const [editStartupMethod, setEditStartupMethod] = useState("");
  const [editStartupType, setEditStartupType] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  const [isAddingStep, setIsAddingStep] = useState(false);
  const [newStepTitle, setNewStepTitle] = useState("");
  const [newStepPhase, setNewStepPhase] = useState("");
  const [statusDialog, setStatusDialog] = useState<{
    isOpen: boolean;
    targetStatus: TemplateStatus;
  }>({ isOpen: false, targetStatus: "DRAFT" });

  const load = useCallback(async () => {
    setIsLoading(true);
    try {
      const data = await fetchTemplateDetail(templateId);
      setTemplate(data);
      setEditTitle(data.title);
      setEditBusinessType(data.business_type);
      setEditStartupMethod(data.startup_method || "");
      setEditStartupType(data.startup_type || "");
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
        startup_method: editStartupMethod || undefined,
        startup_type: editStartupType || undefined,
      });
      await load();
    } catch {
      alert("저장에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleStatusChange = async (newStatus: TemplateStatus, reason?: string) => {
    if (!template) return;
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
      throw err;
    }
  };

  const handleAddStep = async () => {
    if (!template || !newStepTitle.trim()) return;
    try {
      await createTemplateStep(template.id, {
        title: newStepTitle.trim(),
        phase: newStepPhase.trim() || "기본",
      });
      setNewStepTitle("");
      setNewStepPhase("");
      setIsAddingStep(false);
      await load();
    } catch {
      alert("단계 추가에 실패했습니다.");
    }
  };

  const handleDragEnd = async (result: DropResult) => {
    if (!template) return;
    if (!result.destination) return;
    if (result.source.index === result.destination.index) return;

    const reordered = Array.from(template.steps);
    const [moved] = reordered.splice(result.source.index, 1);
    reordered.splice(result.destination.index, 0, moved);

    // Optimistic update
    setTemplate({ ...template, steps: reordered });

    try {
      await reorderTemplateSteps(
        template.id,
        reordered.map((s) => s.id),
      );
      await load();
    } catch {
      alert("순서 변경에 실패했습니다.");
      await load();
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
            {template.startup_type && ` / ${template.startup_type}`}
          </p>
        </div>

        {/* Status actions */}
        <div className="flex gap-2">
          {rejectAction && (
            <Button
              variant="outline"
              size="sm"
              className="text-red-600"
              onClick={() =>
                setStatusDialog({ isOpen: true, targetStatus: rejectAction.value })
              }
            >
              {rejectAction.label}
            </Button>
          )}
          {nextAction && (
            <Button
              size="sm"
              className="gap-2 bg-blue-600 hover:bg-blue-700"
              onClick={() =>
                setStatusDialog({ isOpen: true, targetStatus: nextAction.value })
              }
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
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
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
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500">
                  창업방식
                </label>
                <input
                  type="text"
                  value={editStartupMethod}
                  onChange={(e) => setEditStartupMethod(e.target.value)}
                  placeholder="예: 프랜차이즈, 독립창업"
                  className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500"
                />
              </div>
              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500">
                  창업형태
                </label>
                <input
                  type="text"
                  value={editStartupType}
                  onChange={(e) => setEditStartupType(e.target.value)}
                  placeholder="예: 개인사업, 법인설립"
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

      {/* Mapping source distribution */}
      {(() => {
        const { counts, total } = computeMappingSourceDistribution(template);
        if (total === 0) return null;
        return (
          <Card>
            <CardContent className="p-4">
              <h2 className="text-sm font-bold text-slate-700 mb-3">매핑 소스 분포</h2>
              <div className="flex flex-wrap gap-3">
                {Object.entries(counts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([src, count]) => {
                    const config = MAPPING_SOURCE_DISPLAY[src];
                    if (!config) return null;
                    const Icon = config.icon;
                    const pct = Math.round((count / total) * 100);
                    return (
                      <div key={src} className="flex items-center gap-2">
                        <span
                          className={cn(
                            "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium border",
                            config.className,
                          )}
                        >
                          <Icon className="w-3.5 h-3.5" />
                          {config.label}
                        </span>
                        <span className="text-sm font-bold text-slate-700">{count}건</span>
                        <span className="text-xs text-slate-400">({pct}%)</span>
                      </div>
                    );
                  })}
              </div>
              <div className="mt-2 flex h-2 w-full overflow-hidden rounded-full bg-slate-100">
                {Object.entries(counts)
                  .sort((a, b) => b[1] - a[1])
                  .map(([src, count]) => {
                    const pct = (count / total) * 100;
                    const colorMap: Record<string, string> = {
                      actionkit_direct: "bg-emerald-400",
                      rag: "bg-blue-400",
                      fallback: "bg-amber-400",
                      llm_generated: "bg-purple-400",
                      template: "bg-indigo-400",
                    };
                    return (
                      <div
                        key={src}
                        className={cn("h-full", colorMap[src] || "bg-slate-300")}
                        style={{ width: `${pct}%` }}
                      />
                    );
                  })}
              </div>
            </CardContent>
          </Card>
        );
      })()}

      {/* Steps */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-bold text-slate-900">
            단계 ({template.steps.length})
          </h2>
          {editable && (
            <Button
              size="sm"
              variant="outline"
              className="gap-1"
              onClick={() => setIsAddingStep(true)}
            >
              <Plus size={14} /> 단계 추가
            </Button>
          )}
        </div>

        {isAddingStep && (
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="grid gap-3 md:grid-cols-2">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-500">단계명</label>
                  <input
                    type="text"
                    value={newStepTitle}
                    onChange={(e) => setNewStepTitle(e.target.value)}
                    placeholder="예: 사업자등록"
                    className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-500">단계 구분</label>
                  <input
                    type="text"
                    value={newStepPhase}
                    onChange={(e) => setNewStepPhase(e.target.value)}
                    placeholder="예: 준비, 실행, 완료"
                    className="h-9 w-full rounded-md border border-slate-200 px-3 text-sm outline-none focus:border-blue-500"
                  />
                </div>
              </div>
              <div className="flex gap-2">
                <Button size="sm" onClick={handleAddStep} disabled={!newStepTitle.trim()}>
                  추가
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setIsAddingStep(false);
                    setNewStepTitle("");
                    setNewStepPhase("");
                  }}
                >
                  취소
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        {editable ? (
          <DragDropContext onDragEnd={handleDragEnd}>
            <Droppable droppableId="template-steps">
              {(provided) => (
                <div
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                  className="space-y-3"
                >
                  {template.steps.map((step, index) => (
                    <Draggable
                      key={step.id}
                      draggableId={String(step.id)}
                      index={index}
                    >
                      {(dragProvided, snapshot) => (
                        <div
                          ref={dragProvided.innerRef}
                          {...dragProvided.draggableProps}
                          className={cn(
                            "transition-shadow",
                            snapshot.isDragging && "shadow-lg ring-1 ring-blue-200 rounded-lg",
                          )}
                        >
                          <TemplateStepEditor
                            step={step}
                            templateId={template.id}
                            editable={editable}
                            onChange={load}
                            dragHandleProps={dragProvided.dragHandleProps}
                          />
                        </div>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </div>
              )}
            </Droppable>
          </DragDropContext>
        ) : (
          template.steps.map((step) => (
            <TemplateStepEditor
              key={step.id}
              step={step}
              templateId={template.id}
              editable={editable}
              onChange={load}
            />
          ))
        )}
      </div>

      {/* Status Change Dialog */}
      <StatusChangeDialog
        isOpen={statusDialog.isOpen}
        onClose={() => setStatusDialog((s) => ({ ...s, isOpen: false }))}
        onConfirm={(reason) => handleStatusChange(statusDialog.targetStatus, reason)}
        currentStatus={template.status}
        targetStatus={statusDialog.targetStatus}
        templateTitle={template.title}
      />
    </div>
  );
}
