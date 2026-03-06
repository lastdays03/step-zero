"use client";

import { useCallback, useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

type ConfirmDialogOptions = {
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  destructive?: boolean;
};

type ConfirmDialogState = ConfirmDialogOptions & {
  onConfirm: () => void | Promise<void>;
};

export function useConfirmDialog() {
  const [dialogState, setDialogState] = useState<ConfirmDialogState | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const openConfirm = useCallback(
    (
      options: ConfirmDialogOptions,
      onConfirm: () => void | Promise<void>,
    ) => {
      setDialogState({
        cancelLabel: "취소",
        confirmLabel: "확인",
        ...options,
        onConfirm,
      });
    },
    [],
  );

  const closeConfirm = useCallback(() => {
    if (!isSubmitting) {
      setDialogState(null);
    }
  }, [isSubmitting]);

  const handleConfirm = useCallback(async () => {
    if (!dialogState) return;

    setIsSubmitting(true);
    try {
      await dialogState.onConfirm();
      setDialogState(null);
    } finally {
      setIsSubmitting(false);
    }
  }, [dialogState]);

  const confirmDialog = (
    <Dialog open={dialogState !== null} onOpenChange={(open) => !open && closeConfirm()}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{dialogState?.title}</DialogTitle>
          {dialogState?.description ? (
            <DialogDescription className="whitespace-pre-line">
              {dialogState.description}
            </DialogDescription>
          ) : null}
        </DialogHeader>
        <DialogFooter>
          <Button
            variant="outline"
            onClick={closeConfirm}
            disabled={isSubmitting}
          >
            {dialogState?.cancelLabel}
          </Button>
          <Button
            variant={dialogState?.destructive ? "destructive" : "default"}
            onClick={() => void handleConfirm()}
            disabled={isSubmitting}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                처리 중...
              </>
            ) : (
              dialogState?.confirmLabel
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );

  return { openConfirm, confirmDialog, isConfirming: isSubmitting };
}
