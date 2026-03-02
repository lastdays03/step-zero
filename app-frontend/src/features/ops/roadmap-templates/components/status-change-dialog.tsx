"use client";

import { ArrowRight, Loader2 } from "lucide-react";
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
import { Textarea } from "@/components/ui/textarea";

import type { TemplateStatus } from "../types";
import { TemplateStatusBadge } from "./template-status-badge";

interface StatusChangeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => Promise<void>;
  currentStatus: TemplateStatus;
  targetStatus: TemplateStatus;
  templateTitle: string;
}

export function StatusChangeDialog({
  isOpen,
  onClose,
  onConfirm,
  currentStatus,
  targetStatus,
  templateTitle,
}: StatusChangeDialogProps) {
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleConfirm = async () => {
    setIsSubmitting(true);
    try {
      await onConfirm(reason || undefined);
      setReason("");
      onClose();
    } catch {
      // error handled by parent
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open && !isSubmitting) {
      setReason("");
      onClose();
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>상태 변경 확인</DialogTitle>
          <DialogDescription>
            &quot;{templateTitle}&quot; 템플릿의 상태를 변경합니다.
          </DialogDescription>
        </DialogHeader>

        <div className="flex items-center justify-center gap-3 py-4">
          <TemplateStatusBadge status={currentStatus} />
          <ArrowRight className="h-4 w-4 text-slate-400" />
          <TemplateStatusBadge status={targetStatus} />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium text-slate-700">
            사유 (선택)
          </label>
          <Textarea
            placeholder="상태 변경 사유를 입력하세요..."
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            rows={3}
            disabled={isSubmitting}
          />
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
            onClick={handleConfirm}
            disabled={isSubmitting}
            className="gap-2 bg-blue-600 hover:bg-blue-700"
          >
            {isSubmitting && <Loader2 className="h-4 w-4 animate-spin" />}
            {isSubmitting ? "변경 중..." : "확인"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
