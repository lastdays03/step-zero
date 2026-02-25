"use client";

import React, { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Loader2, Megaphone, AlertCircle } from "lucide-react";

import type { OpsAnnouncement } from "../types";

interface AnnouncementModalProps {
  announcement: OpsAnnouncement | null;
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (data: {
    title: string;
    content: string;
    publish: boolean;
  }) => Promise<void>;
}

export function AnnouncementModal({
  announcement,
  isOpen,
  onClose,
  onConfirm,
}: AnnouncementModalProps) {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (announcement) {
      setTitle(announcement.title);
      setContent(announcement.content);
    } else {
      setTitle("");
      setContent("");
    }
    setError(null);
  }, [announcement, isOpen]);

  const handleSubmit = async (publish: boolean) => {
    if (!title.trim() || !content.trim()) {
      setError("제목과 내용을 모두 입력해주세요.");
      return;
    }

    setIsSubmitting(true);
    setError(null);
    try {
      await onConfirm({ title, content, publish });
      onClose();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "저장에 실패했습니다.",
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-xl font-bold">
            <Megaphone className="text-blue-600" size={20} />
            {announcement ? "공지사항 수정" : "새 공지사항 작성"}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-700">제목</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="공지사항 제목을 입력하세요"
              className="h-10 w-full rounded-md border border-slate-200 px-3 outline-none transition-all placeholder:text-slate-400 focus:border-blue-500"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-bold text-slate-700">내용</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="공지사항 내용을 입력하세요"
              rows={10}
              className="w-full resize-none rounded-md border border-slate-200 p-3 outline-none transition-all placeholder:text-slate-400 focus:border-blue-500"
            />
          </div>

          {error && (
            <div className="flex items-center gap-2 rounded-md bg-red-50 p-3 text-sm text-red-600">
              <AlertCircle size={16} />
              {error}
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button variant="outline" onClick={onClose} disabled={isSubmitting}>
            취소
          </Button>
          <div className="flex gap-2">
            <Button
              variant="outline"
              className="border-blue-200 text-blue-600 hover:bg-blue-50"
              onClick={() => handleSubmit(false)}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                "초안 저장"
              )}
            </Button>
            <Button
              className="bg-blue-600 font-bold hover:bg-blue-700"
              onClick={() => handleSubmit(true)}
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : announcement?.status === "published" ? (
                "수정 완료"
              ) : (
                "게시하기"
              )}
            </Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
