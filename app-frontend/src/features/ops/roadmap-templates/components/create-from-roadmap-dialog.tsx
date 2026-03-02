"use client";

import { Loader2 } from "lucide-react";
import React, { useState } from "react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

import { createTemplateFromRoadmap } from "../api";

interface CreateFromRoadmapDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export function CreateFromRoadmapDialog({
  isOpen,
  onClose,
  onCreated,
}: CreateFromRoadmapDialogProps) {
  const [roadmapId, setRoadmapId] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async () => {
    const trimmed = roadmapId.trim();
    if (!trimmed) {
      setError("로드맵 UUID를 입력하세요.");
      return;
    }
    setError("");
    setIsSubmitting(true);
    try {
      await createTemplateFromRoadmap(trimmed);
      setRoadmapId("");
      onCreated();
      onClose();
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "템플릿 생성에 실패했습니다. UUID를 확인해주세요.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open && !isSubmitting) {
      setRoadmapId("");
      setError("");
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>로드맵에서 템플릿 생성</DialogTitle>
          <DialogDescription>
            기존 로드맵의 UUID를 입력하면 해당 로드맵을 기반으로 새 템플릿을
            생성합니다.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">
            로드맵 UUID
          </label>
          <Input
            placeholder="예: 550e8400-e29b-41d4-a716-446655440000"
            value={roadmapId}
            onChange={(e) => {
              setRoadmapId(e.target.value);
              if (error) setError("");
            }}
            disabled={isSubmitting}
          />
          {error && (
            <p className="text-sm text-red-500">{error}</p>
          )}
        </div>

        <DialogFooter>
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isSubmitting}
          >
            취소
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !roadmapId.trim()}
            className="gap-2 bg-blue-600 hover:bg-blue-700"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "생성 중..." : "생성"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
