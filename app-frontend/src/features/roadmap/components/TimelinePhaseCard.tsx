"use client";

import { useState, useRef } from "react";
import { Check, Lock, ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { TimelineStepItem } from "./TimelineStepItem";
import { MilestoneCelebration } from "./MilestoneCelebration";
import { deriveStepItemState, formatDate, computeReadinessLevel, TOGGLE_ACTION_TYPES } from "./roadmap-utils";
import type { EnhancedPhaseGroup, ReadinessInfo } from "./roadmap-utils";

interface TimelinePhaseCardProps {
    group: EnhancedPhaseGroup;
    roadmapId: string;
    lastCompletedStepId: number | null;
    overallProgress?: number;
    onStepStatusChange: (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => Promise<void>;
    onActionCompletionChange: (stepId: number, actionId: number, completed: boolean) => Promise<void>;
    updatingStepId: number | null;
    updatingActionId: number | null;
}

const STATE_CONFIG = {
    COMPLETED: {
        dotClass: "w-4 h-4 rounded-full bg-green-500 border-4 border-white shadow",
        badgeClass: "bg-green-100 text-green-700",
        badgeLabel: "Completed",
        cardClass: "opacity-70 hover:opacity-100 transition-opacity",
        borderClass: "border border-slate-200",
    },
    CURRENT: {
        dotClass: "w-5 h-5 rounded-full bg-[#36a4f2] border-4 border-white shadow-lg shadow-[#36a4f2]/30 ring-4 ring-[#36a4f2]/10",
        badgeClass: "bg-[#36a4f2]/10 text-[#36a4f2]",
        badgeLabel: "Current Phase",
        cardClass: "",
        borderClass: "border-2 border-[#36a4f2]/20 shadow-xl shadow-[#36a4f2]/5",
    },
    LOCKED: {
        dotClass: "w-4 h-4 rounded-full bg-slate-300 border-4 border-white shadow",
        badgeClass: "bg-slate-100 text-slate-500",
        badgeLabel: "Locked",
        cardClass: "opacity-50",
        borderClass: "border border-slate-200 border-dashed",
    },
    FUTURE: {
        dotClass: "w-4 h-4 rounded-full bg-slate-200 border-4 border-white",
        badgeClass: "bg-slate-100 text-slate-400",
        badgeLabel: "",
        cardClass: "opacity-40",
        borderClass: "border border-slate-100 border-dashed",
    },
} as const;

function LockedStepList({ steps }: { steps: EnhancedPhaseGroup["steps"] }) {
    return (
        <ul className="mt-3 space-y-1.5">
            {steps.map((step) => (
                <li key={step.id} className="flex items-center gap-2 text-sm text-slate-400">
                    <div className="w-4 h-4 rounded-full border border-slate-200 border-dashed flex-shrink-0" />
                    <span className="truncate">{step.title}</span>
                </li>
            ))}
        </ul>
    );
}

function computeChecklistProgress(steps: EnhancedPhaseGroup["steps"]) {
    let total = 0;
    let completed = 0;
    for (const step of steps) {
        const actions = step.detail?.actions ?? [];
        for (const action of actions) {
            if (TOGGLE_ACTION_TYPES.has(action.action_type)) {
                total++;
                if (action.metadata_json?.completed) completed++;
            }
        }
    }
    const percent = total > 0 ? Math.round((completed / total) * 100) : 0;
    return { completed, total, percent };
}

export function TimelinePhaseCard({
    group,
    roadmapId,
    lastCompletedStepId,
    overallProgress,
    onStepStatusChange,
    onActionCompletionChange,
    updatingStepId,
    updatingActionId,
}: TimelinePhaseCardProps) {
    const [expanded, setExpanded] = useState(false);
    const [showAllSteps, setShowAllSteps] = useState(false);
    const [celebration, setCelebration] = useState<"phase" | "step" | null>(null);
    const [prevState, setPrevState] = useState(group.state);
    const [celebrationPrevReadiness, setCelebrationPrevReadiness] = useState<ReadinessInfo | null>(null);
    const config = STATE_CONFIG[group.state];

    // Track readiness level across renders for phase celebration (state-based, no refs during render)
    const currentReadiness = overallProgress != null ? computeReadinessLevel(overallProgress) : null;
    const [trackedReadiness, setTrackedReadiness] = useState<ReadinessInfo | null>(currentReadiness);
    const lastInsightTimeRef = useRef(0);

    // Detect CURRENT → COMPLETED phase transition (state adjustment during render)
    if (prevState !== group.state) {
        setPrevState(group.state);
        if (prevState === "CURRENT" && group.state === "COMPLETED") {
            setCelebrationPrevReadiness(trackedReadiness);
            setCelebration("phase");
        }
    }

    // Track readiness level changes (state update during render pattern)
    if (currentReadiness && trackedReadiness?.level !== currentReadiness.level) {
        setTrackedReadiness(currentReadiness);
    }

    // Wrap step status change to trigger step insight toast (20% chance, 30s cooldown)
    const handleStepStatusChange = async (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => {
        await onStepStatusChange(stepId, status);
        const now = Date.now();
        if (status === "COMPLETED" && Math.random() < 0.2 && now - lastInsightTimeRef.current > 30_000) {
            lastInsightTimeRef.current = now;
            setCelebration("step");
        }
    };

    // FUTURE: step 목록 포함
    if (group.state === "FUTURE") {
        return (
            <div className={cn("relative pl-16", config.cardClass)}>
                <div className={cn("absolute left-6 top-6 z-10 -translate-x-1/2", config.dotClass)} />
                <div className={cn("bg-white rounded-2xl p-6 shadow-sm", config.borderClass)}>
                    <h3 className="text-lg font-medium text-slate-400">{group.phase}</h3>
                    <LockedStepList steps={group.steps} />
                </div>
            </div>
        );
    }

    // LOCKED: step 목록 포함
    if (group.state === "LOCKED") {
        return (
            <div className={cn("relative pl-16", config.cardClass)}>
                <div className={cn("absolute left-6 top-8 z-10 -translate-x-1/2", config.dotClass)} />
                <div className={cn("bg-white rounded-2xl p-6 shadow-sm", config.borderClass)}>
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Badge className={cn("rounded-full text-xs font-bold uppercase tracking-wider", config.badgeClass)}>
                                {config.badgeLabel}
                            </Badge>
                            <h3 className="text-xl font-bold text-slate-800">{group.phase}</h3>
                        </div>
                        <Lock className="w-5 h-5 text-slate-400" />
                    </div>
                    <p className="mt-2 text-slate-500 text-sm">
                        이전 단계를 완료하여 이 단계를 잠금 해제하세요.
                    </p>
                    <LockedStepList steps={group.steps} />
                </div>
            </div>
        );
    }

    // COMPLETED: collapsible card
    if (group.state === "COMPLETED") {
        return (
            <>
                <div className={cn("relative pl-16", config.cardClass)}>
                    <div className={cn("absolute left-6 top-8 z-10 -translate-x-1/2", config.dotClass)} />
                    <div className={cn("bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow", config.borderClass)}>
                        <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-3">
                                <Badge className={cn("rounded-full text-xs font-bold uppercase tracking-wider", config.badgeClass)}>
                                    {config.badgeLabel}
                                </Badge>
                                <h3 className="text-xl font-bold text-slate-800">{group.phase}</h3>
                            </div>
                            <button
                                type="button"
                                onClick={() => setExpanded(!expanded)}
                                className="text-slate-400 hover:text-[#36a4f2] transition-colors"
                            >
                                {expanded ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
                            </button>
                        </div>
                        <div className="flex items-center gap-2 text-slate-500 text-sm">
                            <Check className="w-4 h-4 text-green-500" />
                            <span>
                                모든 과제가 완료되었습니다
                                {group.completedAt ? ` (${formatDate(group.completedAt)} 완료)` : ""}
                            </span>
                        </div>
                        {expanded ? (
                            <div className="mt-4 space-y-2">
                                {group.steps.map((step) => (
                                    <TimelineStepItem
                                        key={step.id}
                                        step={step}
                                        state="DONE"
                                        roadmapId={roadmapId}
                                        canRevert={step.id === lastCompletedStepId}
                                        onStepStatusChange={handleStepStatusChange}
                                        onActionCompletionChange={onActionCompletionChange}
                                        updatingStepId={updatingStepId}
                                        updatingActionId={updatingActionId}
                                    />
                                ))}
                            </div>
                        ) : null}
                    </div>
                </div>
                {celebration && (
                    <MilestoneCelebration
                        type={celebration}
                        phaseName={group.phase}
                        previousReadiness={celebrationPrevReadiness ? `${celebrationPrevReadiness.emoji} ${celebrationPrevReadiness.label}` : null}
                        currentReadiness={currentReadiness ? `${currentReadiness.emoji} ${currentReadiness.label}` : null}
                        onClose={() => setCelebration(null)}
                    />
                )}
            </>
        );
    }

    // CURRENT: focused view — show done summaries + next 3 actionable steps
    const checklist = computeChecklistProgress(group.steps);

    const activeIndex = group.steps.findIndex(
        (s) => s.status === "IN_PROGRESS" || s.status === "PENDING",
    );
    const allDone = activeIndex === -1;
    const doneSteps = allDone ? group.steps : group.steps.slice(0, activeIndex);
    const actionableSteps = allDone ? [] : group.steps.slice(activeIndex);

    const FOCUS_COUNT = 3;
    const needsToggle = !allDone && actionableSteps.length > FOCUS_COUNT;
    const visibleActionable = showAllSteps || !needsToggle
        ? actionableSteps
        : actionableSteps.slice(0, FOCUS_COUNT);
    const hiddenCount = needsToggle ? actionableSteps.length - FOCUS_COUNT : 0;

    return (
        <>
            <div className="relative pl-16" data-phase="current">
                <div className={cn("absolute left-6 top-8 z-10 -translate-x-1/2", config.dotClass)} />
                <div className={cn("bg-white rounded-2xl p-6 lg:p-8 relative overflow-hidden", config.borderClass)}>
                    {/* Background decoration */}
                    <div className="absolute top-0 right-0 -mt-10 -mr-10 w-40 h-40 bg-[#36a4f2]/5 rounded-full blur-3xl" />

                    <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4 relative">
                        <div>
                            <Badge className={cn("rounded-full text-xs font-bold uppercase tracking-wider mb-2", config.badgeClass)}>
                                {config.badgeLabel}
                            </Badge>
                            <h3 className="text-2xl font-bold text-slate-900">{group.phase}</h3>
                            {group.objective ? (
                                <p className="text-slate-500 text-sm mt-1">{group.objective}</p>
                            ) : null}
                        </div>
                        {checklist.total > 0 ? (
                            <div className="flex items-center gap-2 flex-shrink-0">
                                <span className="text-sm font-medium text-slate-600">
                                    체크리스트 {checklist.completed}/{checklist.total}
                                </span>
                                <Progress
                                    value={checklist.percent}
                                    className="w-24 h-2 bg-slate-100"
                                    indicatorClassName="bg-[#36a4f2]"
                                />
                            </div>
                        ) : null}
                    </div>

                    <div className="space-y-4 relative">
                        {/* Completed steps: compact one-line summaries */}
                        {doneSteps.length > 0 && (
                            <div className="space-y-1.5 mb-2">
                                {doneSteps.map((step) => (
                                    <div key={step.id} className="flex items-center gap-2 py-1.5 px-3 rounded-lg bg-slate-50">
                                        <Check className="w-4 h-4 text-green-500 flex-shrink-0" />
                                        <span className="text-sm text-slate-500 truncate">{step.title}</span>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Visible actionable steps */}
                        {visibleActionable.map((step) => {
                            const globalIdx = group.steps.indexOf(step);
                            const hasInProgress = group.steps.some((s) => s.status === "IN_PROGRESS");
                            const isNextActionable = !hasInProgress
                                && step.status === "PENDING"
                                && group.steps.slice(0, globalIdx).every((s) => s.status === "COMPLETED");
                            const state = deriveStepItemState(step, "CURRENT", isNextActionable);
                            const prevStep = globalIdx > 0 ? group.steps[globalIdx - 1] : undefined;
                            return (
                                <TimelineStepItem
                                    key={step.id}
                                    step={step}
                                    state={state}
                                    roadmapId={roadmapId}
                                    canRevert={state === "DONE" && step.id === lastCompletedStepId}
                                    previousStepTitle={state === "LOCKED" ? prevStep?.title : undefined}
                                    onStepStatusChange={handleStepStatusChange}
                                    onActionCompletionChange={onActionCompletionChange}
                                    updatingStepId={updatingStepId}
                                    updatingActionId={updatingActionId}
                                />
                            );
                        })}

                        {/* Toggle button for remaining steps */}
                        {needsToggle && (
                            <button
                                type="button"
                                onClick={() => setShowAllSteps(!showAllSteps)}
                                className="flex items-center gap-1.5 text-sm font-medium text-slate-500 hover:text-[#36a4f2] transition-colors mx-auto py-2"
                            >
                                {showAllSteps ? (
                                    <>접기 <ChevronUp className="w-4 h-4" /></>
                                ) : (
                                    <>나머지 {hiddenCount}개 단계 보기 <ChevronDown className="w-4 h-4" /></>
                                )}
                            </button>
                        )}
                    </div>
                </div>
            </div>
            {celebration && (
                <MilestoneCelebration
                    type={celebration}
                    phaseName={group.phase}
                    onClose={() => setCelebration(null)}
                />
            )}
        </>
    );
}
