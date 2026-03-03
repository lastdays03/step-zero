"use client";

import { useEffect, useRef, useMemo, useState } from "react";
import { RoadmapHeader } from "./RoadmapHeader";
import { TimelinePhaseCard } from "./TimelinePhaseCard";
import { RoadmapSidebar } from "./RoadmapSidebar";
import { derivePhaseGroups, computeEndowedProgress } from "./roadmap-utils";
import type { RoadmapDetailResponse } from "./roadmap-utils";

// Re-export types for backward compatibility
export type { RoadmapDetailAction, RoadmapDetailStep, RoadmapDetailResponse } from "./roadmap-utils";

interface RoadmapExecutionViewProps {
    data: RoadmapDetailResponse;
    onStepStatusChange: (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => Promise<void>;
    onActionCompletionChange: (stepId: number, actionId: number, completed: boolean) => Promise<void>;
    updatingStepId: number | null;
    updatingActionId: number | null;
    hideHeader?: boolean;
}

export const RoadmapExecutionView = ({
    data,
    onStepStatusChange,
    onActionCompletionChange,
    updatingStepId,
    updatingActionId,
    hideHeader,
}: RoadmapExecutionViewProps) => {
    const phaseGroups = useMemo(() => derivePhaseGroups(data.steps), [data.steps]);

    const totalCompleted = data.steps.filter((s) => s.status === "COMPLETED").length;
    const endowed = computeEndowedProgress(totalCompleted, data.steps.length);
    const currentPhase = phaseGroups.find((g) => g.state === "CURRENT");

    // Find the last completed step (only that step can be reverted)
    const lastCompletedStepId = useMemo(() => {
        const completedSteps = data.steps.filter((s) => s.status === "COMPLETED");
        return completedSteps.length > 0
            ? completedSteps[completedSteps.length - 1].id
            : null;
    }, [data.steps]);

    const timelineRef = useRef<HTMLDivElement>(null);
    const [hasScrolled, setHasScrolled] = useState(false);

    useEffect(() => {
        if (hasScrolled) return;
        const container = timelineRef.current;
        if (!container) return;
        const currentEl = container.querySelector<HTMLElement>('[data-phase="current"]');
        if (!currentEl) return;

        // Delay to ensure layout is settled
        const timer = setTimeout(() => {
            const containerRect = container.getBoundingClientRect();
            const elementRect = currentEl.getBoundingClientRect();
            const offset = elementRect.top - containerRect.top + container.scrollTop - 16;
            container.scrollTo({ top: offset, behavior: "smooth" });
            setHasScrolled(true);
        }, 100);
        return () => clearTimeout(timer);
    }, [phaseGroups, hasScrolled]);

    return (
        <section>
            {!hideHeader && (
                <RoadmapHeader
                    title={data.title}
                    currentPhaseName={currentPhase?.phase ?? null}
                />
            )}

            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 relative lg:h-[calc(100vh-220px)]">
                {/* Timeline Section */}
                <div ref={timelineRef} className="lg:col-span-8 lg:overflow-y-auto lg:pr-2 scrollbar-thin">
                    <div className="space-y-8 relative pl-0">
                        {/* Vertical timeline line */}
                        <div
                            className="absolute top-0 bottom-0 left-[2rem] w-0.5 bg-slate-200 z-0 hidden lg:block"
                            aria-hidden="true"
                        />

                        {phaseGroups.map((group) => (
                            <TimelinePhaseCard
                                key={group.phase}
                                group={group}
                                roadmapId={data.roadmap_id}
                                lastCompletedStepId={lastCompletedStepId}
                                overallProgress={endowed.display}
                                onStepStatusChange={onStepStatusChange}
                                onActionCompletionChange={onActionCompletionChange}
                                updatingStepId={updatingStepId}
                                updatingActionId={updatingActionId}
                            />
                        ))}
                    </div>
                </div>

                {/* Right Sidebar */}
                <div className="lg:col-span-4 lg:overflow-y-auto lg:pr-2 scrollbar-thin">
                    <RoadmapSidebar
                        createdAt={data.created_at}
                        steps={data.steps}
                        overallProgress={endowed.display}
                        completedSteps={totalCompleted}
                        totalSteps={data.steps.length}
                    />
                </div>
            </div>
        </section>
    );
};
