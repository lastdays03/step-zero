"use client";

import { useState } from "react";
import { Check, Lock, ChevronDown, ChevronUp } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import { TimelineStepItem } from "./TimelineStepItem";
import { deriveStepItemState, formatDate, TOGGLE_ACTION_TYPES } from "./roadmap-utils";
import type { EnhancedPhaseGroup } from "./roadmap-utils";

interface TimelinePhaseCardProps {
    group: EnhancedPhaseGroup;
    lastCompletedStepId: number | null;
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
    lastCompletedStepId,
    onStepStatusChange,
    onActionCompletionChange,
    updatingStepId,
    updatingActionId,
}: TimelinePhaseCardProps) {
    const [expanded, setExpanded] = useState(false);
    const config = STATE_CONFIG[group.state];

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
                                    canRevert={step.id === lastCompletedStepId}
                                    onStepStatusChange={onStepStatusChange}
                                    onActionCompletionChange={onActionCompletionChange}
                                    updatingStepId={updatingStepId}
                                    updatingActionId={updatingActionId}
                                />
                            ))}
                        </div>
                    ) : null}
                </div>
            </div>
        );
    }

    // CURRENT: fully expanded card with scroll anchor
    const checklist = computeChecklistProgress(group.steps);

    return (
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
                    {group.steps.map((step, idx) => {
                        const hasInProgress = group.steps.some((s) => s.status === "IN_PROGRESS");
                        const isNextActionable = !hasInProgress
                            && step.status === "PENDING"
                            && group.steps.slice(0, idx).every((s) => s.status === "COMPLETED");
                        const state = deriveStepItemState(step, "CURRENT", isNextActionable);
                        const prevStep = idx > 0 ? group.steps[idx - 1] : undefined;
                        return (
                            <TimelineStepItem
                                key={step.id}
                                step={step}
                                state={state}
                                canRevert={state === "DONE" && step.id === lastCompletedStepId}
                                previousStepTitle={state === "LOCKED" ? prevStep?.title : undefined}
                                onStepStatusChange={onStepStatusChange}
                                onActionCompletionChange={onActionCompletionChange}
                                updatingStepId={updatingStepId}
                                updatingActionId={updatingActionId}
                            />
                        );
                    })}
                </div>
            </div>
        </div>
    );
}
