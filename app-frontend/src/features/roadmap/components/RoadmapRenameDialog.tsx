"use client";

import { useRef, useState } from "react";
import {
    Dialog,
    DialogContent,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface RoadmapRenameDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    currentTitle: string;
    onConfirm: (newTitle: string) => void;
    loading?: boolean;
}

export function RoadmapRenameDialog({
    open,
    onOpenChange,
    currentTitle,
    onConfirm,
    loading,
}: RoadmapRenameDialogProps) {
    const [title, setTitle] = useState(currentTitle);
    const inputRef = useRef<HTMLInputElement>(null);

    const handleOpenChange = (nextOpen: boolean) => {
        if (nextOpen) {
            setTitle(currentTitle);
        }
        onOpenChange(nextOpen);
    };

    const canSubmit = title.trim().length > 0 && !loading;

    const handleSubmit = () => {
        const trimmed = title.trim();
        if (trimmed.length > 0) {
            onConfirm(trimmed);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter" && canSubmit) {
            handleSubmit();
        }
    };

    return (
        <Dialog open={open} onOpenChange={handleOpenChange}>
            <DialogContent
                className="sm:max-w-md"
                onOpenAutoFocus={(e) => {
                    e.preventDefault();
                    requestAnimationFrame(() => {
                        const el = inputRef.current;
                        if (el) {
                            el.focus();
                            el.select();
                        }
                    });
                }}
            >
                <DialogHeader>
                    <DialogTitle>로드맵 이름 변경</DialogTitle>
                </DialogHeader>

                <input
                    ref={inputRef}
                    type="text"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="로드맵 이름을 입력하세요"
                    className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                />

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={loading}
                    >
                        취소
                    </Button>
                    <Button onClick={handleSubmit} disabled={!canSubmit}>
                        {loading ? "저장 중..." : "저장"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
