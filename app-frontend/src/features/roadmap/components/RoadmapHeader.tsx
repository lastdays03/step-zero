"use client";

import { ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface RoadmapHeaderProps {
    title: string;
    currentPhaseName: string | null;
    onSwitcherToggle?: () => void;
    roadmapCount?: number;
}

export function RoadmapHeader({
    title,
    currentPhaseName,
    onSwitcherToggle,
    roadmapCount,
}: RoadmapHeaderProps) {
    return (
        <div className="mb-10">
            <div className="flex items-center gap-2 mb-3">
                <h1 className="text-3xl md:text-4xl font-bold text-slate-900">
                    나의 로드맵
                </h1>
                {onSwitcherToggle ? (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={onSwitcherToggle}
                        className="gap-1 text-slate-500 hover:text-slate-700"
                    >
                        <ChevronDown className="h-4 w-4" />
                        {roadmapCount != null ? (
                            <Badge variant="secondary" className="ml-0.5">
                                {roadmapCount}
                            </Badge>
                        ) : null}
                    </Button>
                ) : null}
            </div>
            <p className="text-slate-500 text-lg">
                {title}
                {currentPhaseName ? (
                    <>
                        , 현재{" "}
                        <span className="text-[#36a4f2] font-semibold">
                            {currentPhaseName}
                        </span>{" "}
                        단계 진행 중입니다.
                    </>
                ) : null}
            </p>
        </div>
    );
}
