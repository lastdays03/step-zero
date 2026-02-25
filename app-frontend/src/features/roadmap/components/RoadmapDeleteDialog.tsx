"use client";

import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface RoadmapDeleteDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    roadmapTitle: string;
    isActiveRoadmap?: boolean;
    onConfirm: () => void;
    loading?: boolean;
}

export function RoadmapDeleteDialog({
    open,
    onOpenChange,
    roadmapTitle,
    isActiveRoadmap,
    onConfirm,
    loading,
}: RoadmapDeleteDialogProps) {
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-md">
                <DialogHeader>
                    <DialogTitle>로드맵 삭제</DialogTitle>
                    <DialogDescription>
                        &apos;{roadmapTitle}&apos; 로드맵을 삭제하시겠습니까? 이
                        작업은 되돌릴 수 없습니다.
                    </DialogDescription>
                </DialogHeader>

                {isActiveRoadmap ? (
                    <p className="text-sm text-amber-600">
                        현재 보고 있는 로드맵입니다. 삭제하면 다른 로드맵으로
                        전환됩니다.
                    </p>
                ) : null}

                <DialogFooter>
                    <Button
                        variant="outline"
                        onClick={() => onOpenChange(false)}
                        disabled={loading}
                    >
                        취소
                    </Button>
                    <Button
                        variant="destructive"
                        onClick={onConfirm}
                        disabled={loading}
                    >
                        {loading ? "삭제 중..." : "삭제"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
