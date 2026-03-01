"use client";

import { ChevronDown, ChevronRight } from "lucide-react";
import React, { useState } from "react";

import type { RoadmapTemplateStep } from "../types";
import { TemplateActionEditor } from "./template-action-editor";

interface TemplateStepEditorProps {
  step: RoadmapTemplateStep;
  templateId: number;
  editable: boolean;
  onActionChange: () => void;
}

export function TemplateStepEditor({
  step,
  templateId,
  editable,
  onActionChange,
}: TemplateStepEditorProps) {
  const [isOpen, setIsOpen] = useState(false);

  const checklists = step.actions.filter((a) => a.action_type === "CHECKLIST");
  const legalBasis = step.actions.filter(
    (a) => a.action_type === "LEGAL_BASIS",
  );
  const documents = step.actions.filter((a) => a.action_type === "DOCUMENT");

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <button
        type="button"
        className="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-slate-50"
        onClick={() => setIsOpen(!isOpen)}
      >
        <div className="flex items-center gap-3">
          {isOpen ? (
            <ChevronDown size={16} className="text-slate-400" />
          ) : (
            <ChevronRight size={16} className="text-slate-400" />
          )}
          <span className="rounded bg-blue-100 px-2 py-0.5 text-xs font-bold text-blue-700">
            {step.phase}
          </span>
          <span className="text-sm font-bold text-slate-900">{step.title}</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-slate-500">
          <span>{step.estimated_days}일</span>
          <span>{step.actions.length}개 액션</span>
        </div>
      </button>

      {isOpen && (
        <div className="border-t border-slate-100 px-4 py-4 space-y-4">
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

          {checklists.length > 0 && (
            <TemplateActionEditor
              label="체크리스트"
              actions={checklists}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onActionChange}
            />
          )}

          {legalBasis.length > 0 && (
            <TemplateActionEditor
              label="법적근거"
              actions={legalBasis}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onActionChange}
            />
          )}

          {documents.length > 0 && (
            <TemplateActionEditor
              label="필요서류"
              actions={documents}
              templateId={templateId}
              stepId={step.id}
              editable={editable}
              onActionChange={onActionChange}
            />
          )}

          {checklists.length === 0 &&
            legalBasis.length === 0 &&
            documents.length === 0 && (
              <p className="text-sm text-slate-400">등록된 액션이 없습니다.</p>
            )}
        </div>
      )}
    </div>
  );
}
