"use client";

import { useState } from "react";
import {
    Check,
    MoreHorizontal,
    Pencil,
    Trash2,
    Plus,
    MapPin,
    Briefcase,
} from "lucide-react";
import {
    Popover,
    PopoverContent,
    PopoverTrigger,
} from "@/components/ui/popover";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { RoadmapDeleteDialog } from "./RoadmapDeleteDialog";
import { RoadmapRenameDialog } from "./RoadmapRenameDialog";
import type { RoadmapSummary } from "../types/roadmap";

interface RoadmapSwitcherProps {
    roadmaps: RoadmapSummary[];
    activeRoadmapId: string | null;
    onSelect: (roadmapId: string) => void;
    onDelete: (roadmapId: string) => void;
    onRename: (roadmapId: string, newTitle: string) => void;
    onCreateNew: () => void;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function RoadmapSwitcher({
    roadmaps,
    activeRoadmapId,
    onSelect,
    onDelete,
    onRename,
    onCreateNew,
    open,
    onOpenChange,
}: RoadmapSwitcherProps) {
    const [deleteTarget, setDeleteTarget] = useState<RoadmapSummary | null>(
        null,
    );
    const [renameTarget, setRenameTarget] = useState<RoadmapSummary | null>(
        null,
    );
    const [deleteLoading, setDeleteLoading] = useState(false);
    const [renameLoading, setRenameLoading] = useState(false);

    const handleDelete = async () => {
        if (!deleteTarget) return;
        setDeleteLoading(true);
        try {
            onDelete(deleteTarget.roadmap_id);
        } finally {
            setDeleteLoading(false);
            setDeleteTarget(null);
        }
    };

    const handleRename = async (newTitle: string) => {
        if (!renameTarget) return;
        setRenameLoading(true);
        try {
            onRename(renameTarget.roadmap_id, newTitle);
        } finally {
            setRenameLoading(false);
            setRenameTarget(null);
        }
    };

    return (
        <>
            <Popover open={open} onOpenChange={onOpenChange}>
                <PopoverTrigger asChild>
                    <span />
                </PopoverTrigger>
                <PopoverContent
                    align="start"
                    className="w-[380px] p-0"
                    sideOffset={8}
                >
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 pt-4 pb-3">
                        <div className="flex items-center gap-2">
                            <span className="text-sm font-semibold text-slate-900">
                                나의 로드맵
                            </span>
                            <Badge variant="secondary">{roadmaps.length}</Badge>
                        </div>
                    </div>

                    <Separator />

                    {/* Roadmap list */}
                    <div className="max-h-[400px] overflow-y-auto py-1">
                        {roadmaps.length === 0 ? (
                            <p className="px-4 py-6 text-center text-sm text-slate-400">
                                로드맵이 없습니다.
                            </p>
                        ) : (
                            roadmaps.map((roadmap) => {
                                const isActive =
                                    roadmap.roadmap_id === activeRoadmapId;
                                const progressPercent = roadmap.progress;

                                return (
                                    <div
                                        key={roadmap.roadmap_id}
                                        className={`flex items-start gap-3 px-4 py-3 cursor-pointer transition-colors hover:bg-slate-50 ${
                                            isActive ? "bg-slate-50" : ""
                                        }`}
                                        onClick={() => {
                                            onSelect(roadmap.roadmap_id);
                                            onOpenChange(false);
                                        }}
                                    >
                                        {/* Check icon */}
                                        <div className="mt-0.5 w-5 shrink-0">
                                            {isActive ? (
                                                <Check className="h-4 w-4 text-blue-500" />
                                            ) : null}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm font-medium text-slate-900 truncate">
                                                {roadmap.title}
                                            </p>
                                            <div className="flex items-center gap-2 mt-0.5 text-xs text-slate-500">
                                                <span className="flex items-center gap-0.5">
                                                    <Briefcase className="h-3 w-3" />
                                                    {roadmap.business_type}
                                                </span>
                                                <span className="flex items-center gap-0.5">
                                                    <MapPin className="h-3 w-3" />
                                                    {roadmap.location}
                                                </span>
                                            </div>
                                            <div className="mt-2 flex items-center gap-2">
                                                <Progress
                                                    value={progressPercent}
                                                    className="h-1.5 flex-1"
                                                />
                                                <span className="text-xs text-slate-400 whitespace-nowrap">
                                                    {progressPercent}% (
                                                    {roadmap.completed_steps}/
                                                    {roadmap.total_steps})
                                                </span>
                                            </div>
                                        </div>

                                        {/* Actions dropdown */}
                                        <div className="mt-0.5 shrink-0">
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button
                                                        variant="ghost"
                                                        size="icon"
                                                        className="h-7 w-7"
                                                        onClick={(e) =>
                                                            e.stopPropagation()
                                                        }
                                                    >
                                                        <MoreHorizontal className="h-4 w-4" />
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end">
                                                    <DropdownMenuItem
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setRenameTarget(
                                                                roadmap,
                                                            );
                                                        }}
                                                    >
                                                        <Pencil className="mr-2 h-4 w-4" />
                                                        이름 변경
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem
                                                        onClick={(e) => {
                                                            e.stopPropagation();
                                                            setDeleteTarget(
                                                                roadmap,
                                                            );
                                                        }}
                                                        className="text-red-600 focus:text-red-600"
                                                    >
                                                        <Trash2 className="mr-2 h-4 w-4" />
                                                        삭제
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>

                    <Separator />

                    {/* Create new button */}
                    <div className="p-2">
                        <Button
                            variant="ghost"
                            className="w-full justify-start gap-2 text-sm text-slate-600 hover:text-slate-900"
                            onClick={() => {
                                onCreateNew();
                                onOpenChange(false);
                            }}
                        >
                            <Plus className="h-4 w-4" />
                            새 로드맵 만들기
                        </Button>
                    </div>
                </PopoverContent>
            </Popover>

            {/* Delete dialog */}
            <RoadmapDeleteDialog
                open={deleteTarget !== null}
                onOpenChange={(open) => {
                    if (!open) setDeleteTarget(null);
                }}
                roadmapTitle={deleteTarget?.title ?? ""}
                isActiveRoadmap={deleteTarget?.roadmap_id === activeRoadmapId}
                onConfirm={handleDelete}
                loading={deleteLoading}
            />

            {/* Rename dialog */}
            <RoadmapRenameDialog
                open={renameTarget !== null}
                onOpenChange={(open) => {
                    if (!open) setRenameTarget(null);
                }}
                currentTitle={renameTarget?.title ?? ""}
                onConfirm={handleRename}
                loading={renameLoading}
            />
        </>
    );
}
