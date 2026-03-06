"use client";

import { Pencil, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useConfirmDialog } from "@/features/ops/shared/confirm-dialog";

import {
  createTemplateAction,
  deleteTemplateAction,
  updateTemplateAction,
} from "../api";
import type { RoadmapTemplateAction } from "../types";

interface TemplateActionEditorProps {
  label: string;
  actionType: "CHECKLIST" | "LEGAL_BASIS" | "DOCUMENT";
  actions: RoadmapTemplateAction[];
  templateId: number;
  stepId: number;
  editable: boolean;
  onActionChange: () => void;
}

export function TemplateActionEditor({
  label,
  actionType,
  actions,
  templateId,
  stepId,
  editable,
  onActionChange,
}: TemplateActionEditorProps) {
  const { openConfirm, confirmDialog } = useConfirmDialog();
  const [isAdding, setIsAdding] = useState(false);
  const [addTitle, setAddTitle] = useState("");
  const [addDescription, setAddDescription] = useState("");
  const [addSourceUrl, setAddSourceUrl] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const [editingActionId, setEditingActionId] = useState<number | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editSourceUrl, setEditSourceUrl] = useState("");

  const handleDelete = (action: RoadmapTemplateAction) => {
    openConfirm(
      {
        title: `"${action.title}" 액션을 삭제하시겠습니까?`,
        confirmLabel: "삭제",
        destructive: true,
      },
      async () => {
        try {
          await deleteTemplateAction(templateId, stepId, action.id);
          onActionChange();
        } catch {
          toast.error("삭제에 실패했습니다.");
        }
      },
    );
  };

  const handleAdd = async () => {
    if (!addTitle.trim()) return;
    setIsSaving(true);
    try {
      await createTemplateAction(templateId, stepId, {
        action_type: actionType,
        title: addTitle.trim(),
        description: addDescription.trim() || undefined,
        source_url: addSourceUrl.trim() || undefined,
      });
      setAddTitle("");
      setAddDescription("");
      setAddSourceUrl("");
      setIsAdding(false);
      onActionChange();
    } catch {
      toast.error("추가에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleCancelAdd = () => {
    setIsAdding(false);
    setAddTitle("");
    setAddDescription("");
    setAddSourceUrl("");
  };

  const handleStartEdit = (action: RoadmapTemplateAction) => {
    setEditingActionId(action.id);
    setEditTitle(action.title);
    setEditDescription(action.description || "");
    setEditSourceUrl(action.source_url || "");
  };

  const handleCancelEdit = () => {
    setEditingActionId(null);
    setEditTitle("");
    setEditDescription("");
    setEditSourceUrl("");
  };

  const handleSaveEdit = async () => {
    if (!editingActionId || !editTitle.trim()) return;
    setIsSaving(true);
    try {
      await updateTemplateAction(templateId, stepId, editingActionId, {
        title: editTitle.trim(),
        description: editDescription.trim(),
        source_url: editSourceUrl.trim() || null,
      });
      handleCancelEdit();
      onActionChange();
    } catch {
      toast.error("수정에 실패했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div>
      <p className="text-xs font-bold text-slate-500">{label}</p>
      <div className="mt-1 space-y-1">
        {actions.map((action) =>
          editingActionId === action.id ? (
            <div
              key={action.id}
              className="space-y-2 rounded-md border border-blue-200 bg-blue-50/50 px-3 py-2"
            >
              <Input
                placeholder="제목 (필수)"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                className="h-8 text-sm"
              />
              <Input
                placeholder="설명 (선택)"
                value={editDescription}
                onChange={(e) => setEditDescription(e.target.value)}
                className="h-8 text-sm"
              />
              <Input
                placeholder="URL (선택)"
                value={editSourceUrl}
                onChange={(e) => setEditSourceUrl(e.target.value)}
                className="h-8 text-sm"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  className="h-7 bg-blue-600 text-xs hover:bg-blue-700"
                  disabled={!editTitle.trim() || isSaving}
                  onClick={handleSaveEdit}
                >
                  {isSaving ? "저장 중..." : "저장"}
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={handleCancelEdit}
                  disabled={isSaving}
                >
                  취소
                </Button>
              </div>
            </div>
          ) : (
            <div
              key={action.id}
              className="flex items-center justify-between rounded-md bg-slate-50 px-3 py-2"
            >
              <div className="flex-1">
                <p className="text-sm text-slate-800">{action.title}</p>
                {action.description && (
                  <p className="text-xs text-slate-500">
                    {action.description}
                  </p>
                )}
                {action.source_url && (
                  <p className="text-xs text-blue-500 underline">
                    {action.source_url}
                  </p>
                )}
              </div>
              {editable && (
                <div className="flex items-center gap-1">
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-slate-400 hover:text-blue-600"
                    onClick={() => handleStartEdit(action)}
                  >
                    <Pencil size={12} />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-red-400 hover:text-red-600"
                    onClick={() => handleDelete(action)}
                  >
                    <Trash2 size={12} />
                  </Button>
                </div>
              )}
            </div>
          ),
        )}
      </div>

      {editable && !isAdding && (
        <button
          type="button"
          className="mt-2 flex items-center gap-1 text-xs text-blue-500 hover:text-blue-700"
          onClick={() => setIsAdding(true)}
        >
          <Plus size={12} />
          추가
        </button>
      )}

      {editable && isAdding && (
        <div className="mt-2 space-y-2 rounded-md border border-slate-200 bg-slate-50/50 px-3 py-2">
          <Input
            placeholder="제목 (필수)"
            value={addTitle}
            onChange={(e) => setAddTitle(e.target.value)}
            className="h-8 text-sm"
            autoFocus
          />
          <Input
            placeholder="설명 (선택)"
            value={addDescription}
            onChange={(e) => setAddDescription(e.target.value)}
            className="h-8 text-sm"
          />
          <Input
            placeholder="URL (선택)"
            value={addSourceUrl}
            onChange={(e) => setAddSourceUrl(e.target.value)}
            className="h-8 text-sm"
          />
          <div className="flex gap-2">
            <Button
              size="sm"
              className="h-7 bg-blue-600 text-xs hover:bg-blue-700"
              disabled={!addTitle.trim() || isSaving}
              onClick={handleAdd}
            >
              {isSaving ? "저장 중..." : "저장"}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 text-xs"
              onClick={handleCancelAdd}
              disabled={isSaving}
            >
              취소
            </Button>
          </div>
        </div>
      )}
      {confirmDialog}
    </div>
  );
}
