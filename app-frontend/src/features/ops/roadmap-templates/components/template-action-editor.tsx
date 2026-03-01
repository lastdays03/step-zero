"use client";

import { Trash2 } from "lucide-react";

import { Button } from "@/components/ui/button";

import { deleteTemplateAction } from "../api";
import type { RoadmapTemplateAction } from "../types";

interface TemplateActionEditorProps {
  label: string;
  actions: RoadmapTemplateAction[];
  templateId: number;
  stepId: number;
  editable: boolean;
  onActionChange: () => void;
}

export function TemplateActionEditor({
  label,
  actions,
  templateId,
  stepId,
  editable,
  onActionChange,
}: TemplateActionEditorProps) {
  const handleDelete = async (action: RoadmapTemplateAction) => {
    if (!confirm(`"${action.title}" 액션을 삭제하시겠습니까?`)) return;
    try {
      await deleteTemplateAction(templateId, stepId, action.id);
      onActionChange();
    } catch {
      alert("삭제에 실패했습니다.");
    }
  };

  return (
    <div>
      <p className="text-xs font-bold text-slate-500">{label}</p>
      <div className="mt-1 space-y-1">
        {actions.map((action) => (
          <div
            key={action.id}
            className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2"
          >
            <div className="flex-1">
              <p className="text-sm text-slate-800">{action.title}</p>
              {action.description && (
                <p className="text-xs text-slate-500">{action.description}</p>
              )}
              {action.source_url && (
                <p className="text-xs text-blue-500 underline">
                  {action.source_url}
                </p>
              )}
            </div>
            {editable && (
              <Button
                variant="ghost"
                size="sm"
                className="text-red-400 hover:text-red-600"
                onClick={() => handleDelete(action)}
              >
                <Trash2 size={12} />
              </Button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
