"use client";

import { useMemo, useState } from "react";

export interface RoadmapDetailAction {
    id: number;
    action_type: string;
    title: string;
    description: string;
    source_url?: string | null;
    metadata_json?: Record<string, unknown>;
}

export interface RoadmapDetailStep {
    id: number;
    title: string;
    status: string;
    detail?: {
        id: number;
        phase: string;
        objective: string;
        estimated_days: number;
        actions: RoadmapDetailAction[];
    } | null;
}

export interface RoadmapDetailResponse {
    roadmap_id: string;
    title: string;
    steps: RoadmapDetailStep[];
}

interface RoadmapExecutionViewProps {
    data: RoadmapDetailResponse;
    onStepStatusChange: (stepId: number, status: "IN_PROGRESS" | "COMPLETED") => Promise<void>;
    onActionCompletionChange: (stepId: number, actionId: number, completed: boolean) => Promise<void>;
    updatingStepId: number | null;
    updatingActionId: number | null;
}

type PhaseGroup = {
    phase: string;
    steps: RoadmapDetailStep[];
    progress: number;
};

const STATUS_LABEL: Record<string, string> = {
    PENDING: "대기",
    IN_PROGRESS: "진행 중",
    COMPLETED: "완료",
    BLOCKED: "보류",
};

const ACTION_TYPE_LABEL: Record<string, string> = {
    CHECKLIST: "체크리스트",
    LEGAL_BASIS: "법적 근거",
    DOCUMENT: "필수 서류",
};

const TOGGLE_ACTION_TYPES = new Set(["CHECKLIST", "DOCUMENT"]);

export const RoadmapExecutionView = ({
    data,
    onStepStatusChange,
    onActionCompletionChange,
    updatingStepId,
    updatingActionId,
}: RoadmapExecutionViewProps) => {
    const phaseGroups = useMemo<PhaseGroup[]>(() => {
        const grouped = new Map<string, RoadmapDetailStep[]>();
        for (const step of data.steps) {
            const phase = step.detail?.phase || "기본";
            const bucket = grouped.get(phase) ?? [];
            bucket.push(step);
            grouped.set(phase, bucket);
        }
        return Array.from(grouped.entries()).map(([phase, steps]) => {
            const completed = steps.filter((step) => step.status === "COMPLETED").length;
            const progress = steps.length ? Math.round((completed / steps.length) * 100) : 0;
            return { phase, steps, progress };
        });
    }, [data.steps]);

    const preferredPhase = useMemo(() => {
        const inProgress = data.steps.find((step) => step.status === "IN_PROGRESS");
        if (inProgress?.detail?.phase) return inProgress.detail.phase;
        const pending = data.steps.find((step) => step.status === "PENDING");
        if (pending?.detail?.phase) return pending.detail.phase;
        const next = data.steps.find((step) => step.status !== "COMPLETED");
        if (next?.detail?.phase) return next.detail.phase;
        return phaseGroups[0]?.phase || "기본";
    }, [data.steps, phaseGroups]);

    const [selectedPhase, setSelectedPhase] = useState<string>(preferredPhase);
    const resolvedSelectedPhase = phaseGroups.some((group) => group.phase === selectedPhase)
        ? selectedPhase
        : preferredPhase;
    const currentPhase = phaseGroups.find((group) => group.phase === resolvedSelectedPhase) ?? phaseGroups[0];
    const totalCompleted = data.steps.filter((step) => step.status === "COMPLETED").length;
    const overallProgress = data.steps.length ? Math.round((totalCompleted / data.steps.length) * 100) : 0;

    return (
        <section className="space-y-6">
            <div className="flex items-start justify-between rounded-2xl border border-slate-200 bg-white p-6">
                <div>
                    <h1 className="text-3xl font-black text-slate-900">나의 로드맵</h1>
                    <p className="mt-2 text-sm text-slate-500">{data.title}</p>
                </div>
                <div className="w-56 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                    <p className="text-xs font-bold text-slate-500">전체 진행률</p>
                    <p className="mt-1 text-2xl font-black text-blue-600">{overallProgress}%</p>
                    <div className="mt-2 h-2 rounded-full bg-slate-200">
                        <div className="h-2 rounded-full bg-blue-500" style={{ width: `${overallProgress}%` }} />
                    </div>
                </div>
            </div>

            <div className="grid gap-6 lg:grid-cols-[220px_1fr_300px]">
                <aside className="rounded-2xl border border-slate-200 bg-white p-4">
                    <p className="mb-3 text-sm font-bold text-slate-700">Phase 타임라인</p>
                    <ul className="space-y-2">
                        {phaseGroups.map((group) => (
                            <li key={group.phase}>
                                <button
                                    type="button"
                                    onClick={() => setSelectedPhase(group.phase)}
                                    className={`w-full rounded-xl border px-3 py-2 text-left ${
                                        resolvedSelectedPhase === group.phase
                                            ? "border-blue-400 bg-blue-50"
                                            : "border-slate-200 bg-white hover:bg-slate-50"
                                    }`}
                                >
                                    <p className="text-sm font-semibold text-slate-900">{group.phase}</p>
                                    <p className="text-xs text-slate-500">{group.progress}% 완료</p>
                                </button>
                            </li>
                        ))}
                    </ul>
                </aside>

                <main className="space-y-3 rounded-2xl border border-slate-200 bg-white p-5">
                    <div className="mb-4">
                        <h2 className="text-xl font-black text-slate-900">{currentPhase?.phase}</h2>
                        <p className="text-sm text-slate-500">단계별 작업을 완료하며 진행률을 올리세요.</p>
                    </div>
                    {(currentPhase?.steps || []).map((step) => (
                        <article key={step.id} className="rounded-xl border border-slate-200 p-4">
                            {(() => {
                                const checklist = step.detail?.actions.filter(
                                    (action) => action.action_type === "CHECKLIST"
                                ) || [];
                                const checklistCompleted = checklist.filter(
                                    (action) => action.metadata_json?.completed === true
                                ).length;
                                const checklistProgress = checklist.length
                                    ? Math.round((checklistCompleted / checklist.length) * 100)
                                    : 0;
                                return (
                                    <div className="mb-2 text-xs font-semibold text-slate-500">
                                        체크리스트 진행률 {checklistCompleted}/{checklist.length} ({checklistProgress}%)
                                    </div>
                                );
                            })()}
                            <div className="flex items-center justify-between">
                                <h3 className="text-base font-bold text-slate-900">{step.title}</h3>
                                <span className="rounded-full bg-slate-100 px-2 py-1 text-xs font-semibold text-slate-600">
                                    {STATUS_LABEL[step.status] || step.status}
                                </span>
                            </div>
                            {step.detail?.objective ? (
                                <p className="mt-2 text-sm text-slate-600">{step.detail.objective}</p>
                            ) : null}
                            {step.detail?.estimated_days ? (
                                <p className="mt-1 text-xs text-slate-500">
                                    예상 소요: {step.detail.estimated_days}일
                                </p>
                            ) : null}

                            {step.detail?.actions?.length ? (
                                <div className="mt-3 grid gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3">
                                    {(["CHECKLIST", "LEGAL_BASIS", "DOCUMENT"] as const).map((actionType) => {
                                        const items = step.detail?.actions.filter(
                                            (action) => action.action_type === actionType
                                        );
                                        if (!items?.length) return null;
                                        return (
                                            <div key={`${step.id}-${actionType}`}>
                                                <p className="mb-1 text-xs font-bold text-slate-700">
                                                    {ACTION_TYPE_LABEL[actionType]}
                                                </p>
                                                <ul className="space-y-1">
                                                    {items.map((item) => (
                                                        <li
                                                            key={item.id}
                                                            className="rounded-lg bg-white px-2 py-1.5 text-xs text-slate-600"
                                                        >
                                                            {TOGGLE_ACTION_TYPES.has(actionType) ? (
                                                                <button
                                                                    type="button"
                                                                    onClick={() =>
                                                                        void onActionCompletionChange(
                                                                            step.id,
                                                                            item.id,
                                                                            !(item.metadata_json?.completed === true)
                                                                        )
                                                                    }
                                                                    disabled={updatingActionId === item.id}
                                                                    className="mr-2 inline-flex h-4 w-4 items-center justify-center rounded border border-slate-300 text-[10px] font-bold text-blue-600 disabled:opacity-50"
                                                                >
                                                                    {item.metadata_json?.completed === true ? "✓" : ""}
                                                                </button>
                                                            ) : null}
                                                            <p className="font-semibold text-slate-800">{item.title}</p>
                                                            {item.description ? (
                                                                <p className="mt-0.5">{item.description}</p>
                                                            ) : null}
                                                            {item.source_url ? (
                                                                <a
                                                                    href={item.source_url}
                                                                    target="_blank"
                                                                    rel="noreferrer"
                                                                    className="mt-1 inline-block text-blue-600 underline"
                                                                >
                                                                    근거/원문 보기
                                                                </a>
                                                            ) : null}
                                                        </li>
                                                    ))}
                                                </ul>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : null}
                            <div className="mt-3 flex gap-2">
                                <button
                                    type="button"
                                    onClick={() => void onStepStatusChange(step.id, "IN_PROGRESS")}
                                    disabled={
                                        updatingStepId === step.id ||
                                        step.status === "IN_PROGRESS" ||
                                        step.status === "COMPLETED"
                                    }
                                    className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 disabled:opacity-50"
                                >
                                    {updatingStepId === step.id ? "처리 중..." : "시작"}
                                </button>
                                <button
                                    type="button"
                                    onClick={() => void onStepStatusChange(step.id, "COMPLETED")}
                                    disabled={updatingStepId === step.id || step.status === "COMPLETED"}
                                    className="rounded-lg bg-blue-600 px-3 py-1.5 text-xs font-semibold text-white disabled:opacity-50"
                                >
                                    {updatingStepId === step.id ? "처리 중..." : "완료"}
                                </button>
                            </div>
                        </article>
                    ))}
                </main>

                <aside className="space-y-4">
                    <section className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm font-bold text-slate-800">현재 상태</p>
                        <p className="mt-2 text-sm text-slate-600">
                            완료 {totalCompleted}/{data.steps.length} 단계
                        </p>
                    </section>
                    <section className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm font-bold text-slate-800">다음 일정</p>
                        <ul className="mt-2 space-y-2 text-sm text-slate-600">
                            {data.steps
                                .filter((step) => step.status !== "COMPLETED")
                                .slice(0, 3)
                                .map((step) => (
                                    <li key={step.id} className="rounded-lg bg-slate-50 px-2 py-1.5">
                                        {step.title}
                                    </li>
                                ))}
                        </ul>
                    </section>
                    <section className="rounded-2xl border border-slate-200 bg-white p-4">
                        <p className="text-sm font-bold text-slate-800">도움이 필요하신가요?</p>
                        <p className="mt-2 text-sm text-slate-600">
                            단계별 가이드와 법적 근거를 먼저 확인하고 진행하세요.
                        </p>
                    </section>
                </aside>
            </div>
        </section>
    );
};
