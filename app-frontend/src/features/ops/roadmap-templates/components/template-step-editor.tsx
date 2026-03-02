"use client";

import {
  AlertCircle,
  BookOpen,
  ChevronDown,
  ChevronRight,
  Database,
  GripVertical,
  Pencil,
  Save,
  Sparkles,
  Trash2,
  X,
} from "lucide-react";
import type { DraggableProvidedDragHandleProps } from "@hello-pangea/dnd";
import React, { useState } from "react";
import { toast } from "sonner";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

import {
  deleteTemplateStep,
  updateTemplateStep,
} from "../api";
import type { RoadmapTemplateAction, RoadmapTemplateStep } from "../types";
import { TemplateActionEditor } from "./template-action-editor";

type MappingSource = "actionkit_direct" | "rag" | "fallback" | "llm_generated" | "template";

const MAPPING_SOURCE_CONFIG: Record<string, { label: string; className: string; icon: typeof BookOpen }> = {
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

function deriveMappingSource(actions: RoadmapTemplateAction[]): MappingSource | null {
  const sources: string[] = [];
  for (const a of actions) {
    const src = a.metadata_json?.mapping_source;
    if (typeof src === "string") sources.push(src);
  }
  if (sources.length === 0) return null;
  const counts: Record<string, number> = {};
  for (const s of sources) {
    counts[s] = (counts[s] || 0) + 1;
  }
  return Object.entries(counts).sort((a, b) => b[1] - a[1])[0][0] as MappingSource;
}

function StepMappingBadge({ source }: { source: MappingSource }) {
  const config = MAPPING_SOURCE_CONFIG[source];
  if (!config) return null;
  const Icon = config.icon;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-medium border",
        config.className,
      )}
    >
      <Icon className="w-3 h-3" />
      {config.label}
    </span>
  );
}

interface TemplateStepEditorProps {
  step: RoadmapTemplateStep;
  templateId: number;
  editable: boolean;
  onChange: () => void;
  dragHandleProps?: DraggableProvidedDragHandleProps | null;
}

export function TemplateStepEditor({
  step,
  templateId,
  editable,
  onChange,
  dragHandleProps,
}: TemplateStepEditorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [isEditingMeta, setIsEditingMeta] = useState(false);
  const [editObjective, setEditObjective] = useState(step.objective);
  const [editRiskNotes, setEditRiskNotes] = useState<string[]>(step.risk_notes);
  const [editTitle, setEditTitle] = useState(step.title);
  const [editPhase, setEditPhase] = useState(step.phase);
  const [editEstDays, setEditEstDays] = useState(step.estimated_days);
  const [isSaving, setIsSaving] = useState(false);

  const checklists = step.actions.filter((a) => a.action_type === "CHECKLIST");
  const legalBasis = step.actions.filter(
    (a) => a.action_type === "LEGAL_BASIS",
  );
  const documents = step.actions.filter((a) => a.action_type === "DOCUMENT");
  const mappingSource = deriveMappingSource(step.actions);

  const handleSaveStep = async () => {
    setIsSaving(true);
    try {
      await updateTemplateStep(templateId, step.id, {
        title: editTitle,
        phase: editPhase,
        objective: editObjective,
        estimated_days: editEstDays,
        risk_notes: editRiskNotes,
      });
      setIsEditingMeta(false);
      onChange();
    } catch {
      toast.error("단계 수정에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteStep = async () => {
    if (!confirm(`"${step.title}" 단계를 삭제하시겠습니까? 하위 액션도 함께 삭제됩니다.`)) return;
    try {
      await deleteTemplateStep(templateId, step.id);
      onChange();
    } catch {
      toast.error("단계 삭제에 실패했습니다.");
    }
  };

  const addRiskNote = () => {
    setEditRiskNotes([...editRiskNotes, ""]);
  };

  const updateRiskNote = (index: number, value: string) => {
    const updated = [...editRiskNotes];
    updated[index] = value;
    setEditRiskNotes(updated);
  };

  const removeRiskNote = (index: number) => {
    setEditRiskNotes(editRiskNotes.filter((_, i) => i !== index));
  };

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-slate-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          {dragHandleProps && (
            <span
              {...dragHandleProps}
              className="cursor-grab text-slate-300 hover:text-slate-500 active:cursor-grabbing"
              onClick={(e) => e.stopPropagation()}
            >
              <GripVertical size={16} />
            </span>
          )}
          {isOpen ? (
            <ChevronDown size={16} className="text-slate-400" />
          ) : (
            <ChevronRight size={16} className="text-slate-400" />
          )}
          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">
            {step.phase}
          </span>
          <span className="text-sm font-bold text-slate-900">{step.title}</span>
          {mappingSource && <StepMappingBadge source={mappingSource} />}
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>{step.estimated_days}일</span>
          <span>{step.actions.length}개 액션</span>
          {editable && (
            <span
              className="text-red-400 hover:text-red-600"
              role="button"
              tabIndex={0}
              onClick={(e) => {
                e.stopPropagation();
                void handleDeleteStep();
              }}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.stopPropagation();
                  void handleDeleteStep();
                }
              }}
            >
              <Trash2 size={14} />
            </span>
          )}
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-slate-100 px-4 py-4 space-y-4">
          {/* Editable step meta */}
          {editable && !isEditingMeta && (
            <div className="flex justify-end">
              <Button
                variant="ghost"
                size="sm"
                className="gap-1 text-xs"
                onClick={() => setIsEditingMeta(true)}
              >
                <Pencil size={12} /> 단계 정보 수정
              </Button>
            </div>
          )}

          {isEditingMeta ? (
            <div className="space-y-3 rounded-md border border-blue-200 bg-blue-50/50 p-3">
              <div className="grid gap-3 md:grid-cols-3">
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-500">단계명</label>
                  <input
                    type="text"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    className="h-8 w-full rounded border border-slate-200 px-2 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-500">단계 구분</label>
                  <input
                    type="text"
                    value={editPhase}
                    onChange={(e) => setEditPhase(e.target.value)}
                    className="h-8 w-full rounded border border-slate-200 px-2 text-sm"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs font-bold text-slate-500">예상 소요일</label>
                  <input
                    type="number"
                    value={editEstDays}
                    onChange={(e) => setEditEstDays(Number(e.target.value))}
                    className="h-8 w-full rounded border border-slate-200 px-2 text-sm"
                  />
                </div>
              </div>

              <div className="space-y-1">
                <label className="text-xs font-bold text-slate-500">목표</label>
                <textarea
                  value={editObjective}
                  onChange={(e) => setEditObjective(e.target.value)}
                  rows={2}
                  className="w-full rounded border border-slate-200 px-2 py-1 text-sm"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-bold text-slate-500">위험사항</label>
                {editRiskNotes.map((note, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      type="text"
                      value={note}
                      onChange={(e) => updateRiskNote(i, e.target.value)}
                      className="h-8 flex-1 rounded border border-slate-200 px-2 text-sm"
                    />
                    <button
                      type="button"
                      className="text-red-400 hover:text-red-600"
                      onClick={() => removeRiskNote(i)}
                    >
                      <X size={14} />
                    </button>
                  </div>
                ))}
                <Button variant="ghost" size="sm" className="text-xs" onClick={addRiskNote}>
                  + 위험사항 추가
                </Button>
              </div>

              <div className="flex gap-2">
                <Button size="sm" className="gap-1" onClick={handleSaveStep} disabled={isSaving}>
                  <Save size={12} /> {isSaving ? "저장 중..." : "저장"}
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => {
                    setIsEditingMeta(false);
                    setEditTitle(step.title);
                    setEditPhase(step.phase);
                    setEditEstDays(step.estimated_days);
                    setEditObjective(step.objective);
                    setEditRiskNotes(step.risk_notes);
                  }}
                >
                  취소
                </Button>
              </div>
            </div>
          ) : (
            <>
              {step.objective && (
                <div>
                  <p className="text-xs font-bold text-slate-500">목표</p>
                  <p className="mt-1 text-sm text-slate-700">{step.objective}</p>
                </div>
              )}

              {step.risk_notes.length > 0 && (
                <div>
                  <p className="text-xs font-bold text-slate-500">위험사항</p>
                  <ul className="mt-1 list-inside list-disc text-sm text-slate-700">
                    {step.risk_notes.map((note, i) => (
                      <li key={i}>{note}</li>
                    ))}
                  </ul>
                </div>
              )}
            </>
          )}

          {(checklists.length > 0 || editable) && (
            <TemplateActionEditor
              label="체크리스트"
              actionType="CHECKLIST"
              actions={checklists}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onChange}
            />
          )}

          {(legalBasis.length > 0 || editable) && (
            <TemplateActionEditor
              label="법적근거"
              actionType="LEGAL_BASIS"
              actions={legalBasis}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onChange}
            />
          )}

          {(documents.length > 0 || editable) && (
            <TemplateActionEditor
              label="필요서류"
              actionType="DOCUMENT"
              actions={documents}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onChange}
            />
          )}

          {!editable &&
            checklists.length === 0 &&
            legalBasis.length === 0 &&
            documents.length === 0 && (
              <p className="text-sm text-slate-400">등록된 액션이 없습니다.</p>
            )}
        </div>
      )}
    </div>
  );
}
