"use client";

import { useState } from "react";
import { Check, Lock, ExternalLink, Undo2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { RoadmapDetailStep, StepItemState } from "./roadmap-utils";
import { TOGGLE_ACTION_TYPES, ACTION_TYPE_LABEL } from "./roadmap-utils";

interface TimelineStepItemProps {
    step: RoadmapDetailStep;
    state: StepItemState;
    previousStepTitle?: string;
    canRevert?: boolean;
    onStepStatusChange: (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => Promise<void>;
    onActionCompletionChange: (stepId: number, actionId: number, completed: boolean) => Promise<void>;
    updatingStepId: number | null;
    updatingActionId: number | null;
}

export function TimelineStepItem({
    step,
    state,
    previousStepTitle,
    canRevert,
    onStepStatusChange,
    onActionCompletionChange,
    updatingStepId,
    updatingActionId,
}: TimelineStepItemProps) {
    const [confirming, setConfirming] = useState(false);

    if (state === "DONE") {
        const isReverting = updatingStepId === step.id;
        return (
            <div className="group flex items-start gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100 hover:border-[#36a4f2]/30 transition-colors">
                <div className="flex-shrink-0 pt-1">
                    <div className="w-6 h-6 rounded-full bg-green-500 text-white flex items-center justify-center shadow-sm">
                        <Check className="w-3.5 h-3.5" />
                    </div>
                </div>
                <div className="flex-grow min-w-0">
                    <h4 className="text-base font-semibold text-slate-900 line-through opacity-50">
                        {step.title}
                    </h4>
                    {step.detail?.objective ? (
                        <p className="text-sm text-slate-500 mt-1 line-through opacity-50">
                            {step.detail.objective}
                        </p>
                    ) : null}
                </div>
                {canRevert ? (
                    <button
                        type="button"
                        onClick={() => void onStepStatusChange(step.id, "IN_PROGRESS")}
                        disabled={isReverting}
                        className="flex items-center gap-1 text-xs font-medium text-slate-400 hover:text-[#36a4f2] transition-colors whitespace-nowrap opacity-0 group-hover:opacity-100 disabled:opacity-50"
                    >
                        <Undo2 className="w-3.5 h-3.5" />
                        {isReverting ? "처리 중..." : "되돌리기"}
                    </button>
                ) : (
                    <span className="text-xs font-medium text-slate-400 whitespace-nowrap hidden sm:block">
                        완료됨
                    </span>
                )}
            </div>
        );
    }

    if (state === "LOCKED") {
        return (
            <div className="group flex items-start gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100/50 border-dashed opacity-70">
                <div className="flex-shrink-0 pt-1">
                    <div className="w-6 h-6 rounded-full border-2 border-slate-200 border-dashed" />
                </div>
                <div className="flex-grow min-w-0">
                    <h4 className="text-base font-semibold text-slate-700">
                        {step.title}
                    </h4>
                    <p className="text-sm text-slate-500 mt-1">
                        {previousStepTitle
                            ? `'${previousStepTitle}' 완료 후 진행 가능`
                            : "이전 단계 완료 후 진행 가능"}
                    </p>
                </div>
                <Lock className="w-4 h-4 text-slate-300 flex-shrink-0" />
            </div>
        );
    }

    // ACTIVE state
    const actions = step.detail?.actions || [];
    const isUpdating = updatingStepId === step.id;

    const handleComplete = () => {
        if (confirming) {
            setConfirming(false);
            void onStepStatusChange(step.id, "COMPLETED");
        } else {
            setConfirming(true);
        }
    };

    return (
        <div className="group flex items-start gap-4 p-4 rounded-xl bg-white border border-[#36a4f2] shadow-sm ring-1 ring-[#36a4f2]/10">
            <div className="flex-shrink-0 pt-1">
                <button
                    type="button"
                    onClick={handleComplete}
                    disabled={isUpdating}
                    className={cn(
                        "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-colors disabled:opacity-50",
                        confirming
                            ? "border-orange-400 bg-orange-50 hover:bg-orange-100"
                            : "border-slate-300 hover:border-[#36a4f2] hover:bg-[#36a4f2]/5",
                    )}
                    title={confirming ? "한 번 더 클릭하면 완료 처리됩니다" : "완료 처리"}
                >
                    {confirming ? <Check className="w-3 h-3 text-orange-500" /> : null}
                </button>
            </div>
            <div className="flex-grow min-w-0">
                <div className="flex items-center gap-2 mb-1">
                    <h4 className="text-base font-bold text-slate-900">
                        {step.title}
                    </h4>
                </div>
                {step.detail?.objective ? (
                    <p className="text-sm text-slate-600 mt-1 mb-3">
                        {step.detail.objective}
                    </p>
                ) : null}

                {actions.length > 0 ? (
                    <div className="space-y-2 mt-3">
                        {(["CHECKLIST", "DOCUMENT", "LEGAL_BASIS"] as const).map((actionType) => {
                            const items = actions.filter((a) => a.action_type === actionType);
                            if (!items.length) return null;
                            return (
                                <div key={actionType}>
                                    <p className="text-xs font-bold text-slate-500 mb-1.5">
                                        {ACTION_TYPE_LABEL[actionType]}
                                    </p>
                                    <ul className="space-y-1.5">
                                        {items.map((item) => {
                                            const isCompleted = item.metadata_json?.completed === true;
                                            const isToggleable = TOGGLE_ACTION_TYPES.has(actionType);
                                            return (
                                                <li
                                                    key={item.id}
                                                    className={cn(
                                                        "rounded-lg px-3 py-2 text-sm",
                                                        isToggleable
                                                            ? "bg-slate-50 hover:bg-slate-100 transition-colors"
                                                            : "bg-slate-50",
                                                    )}
                                                >
                                                    <div className="flex items-start gap-2">
                                                        {isToggleable ? (
                                                            <button
                                                                type="button"
                                                                onClick={() =>
                                                                    void onActionCompletionChange(
                                                                        step.id,
                                                                        item.id,
                                                                        !isCompleted,
                                                                    )
                                                                }
                                                                disabled={updatingActionId === item.id}
                                                                className={cn(
                                                                    "mt-0.5 flex-shrink-0 w-5 h-5 rounded border-2 flex items-center justify-center transition-colors disabled:opacity-50",
                                                                    isCompleted
                                                                        ? "bg-[#36a4f2] border-[#36a4f2] text-white"
                                                                        : "border-slate-300 hover:border-[#36a4f2]",
                                                                )}
                                                            >
                                                                {isCompleted ? <Check className="w-3 h-3" /> : null}
                                                            </button>
                                                        ) : null}
                                                        <div className="min-w-0 flex-grow">
                                                            <p className={cn(
                                                                "font-medium text-slate-800",
                                                                isCompleted && "line-through opacity-50",
                                                            )}>
                                                                {item.title}
                                                            </p>
                                                            {item.description ? (
                                                                <p className="text-xs text-slate-500 mt-0.5">
                                                                    {item.description}
                                                                </p>
                                                            ) : null}
                                                            {item.source_url ? (
                                                                <a
                                                                    href={item.source_url}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    className="inline-flex items-center gap-1 mt-1 text-xs text-[#36a4f2] hover:underline"
                                                                >
                                                                    근거/원문 보기
                                                                    <ExternalLink className="w-3 h-3" />
                                                                </a>
                                                            ) : null}
                                                        </div>
                                                    </div>
                                                </li>
                                            );
                                        })}
                                    </ul>
                                </div>
                            );
                        })}
                    </div>
                ) : null}

                <div className="flex items-center gap-3 mt-4">
                    {confirming ? (
                        <>
                            <button
                                type="button"
                                onClick={handleComplete}
                                disabled={isUpdating}
                                className="px-4 py-2 bg-[#36a4f2] hover:bg-[#2b83c2] text-white text-sm font-medium rounded-lg shadow-sm shadow-[#36a4f2]/30 transition-all disabled:opacity-50 flex items-center gap-2"
                            >
                                {isUpdating ? "처리 중..." : "완료 확인"}
                            </button>
                            <button
                                type="button"
                                onClick={() => setConfirming(false)}
                                disabled={isUpdating}
                                className="px-4 py-2 text-slate-600 hover:text-slate-800 text-sm font-medium rounded-lg border border-slate-200 hover:border-slate-300 transition-all disabled:opacity-50"
                            >
                                취소
                            </button>
                            <span className="text-xs text-orange-500 font-medium">
                                정말 완료 처리하시겠습니까?
                            </span>
                        </>
                    ) : (
                        <button
                            type="button"
                            onClick={handleComplete}
                            disabled={isUpdating}
                            className="px-4 py-2 bg-[#36a4f2] hover:bg-[#2b83c2] text-white text-sm font-medium rounded-lg shadow-sm shadow-[#36a4f2]/30 transition-all disabled:opacity-50 flex items-center gap-2"
                        >
                            {isUpdating ? "처리 중..." : "완료 처리"}
                        </button>
                    )}
                </div>
            </div>
        </div>
    );
}
