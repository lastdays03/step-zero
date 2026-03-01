import { ENDOWED_STEPS, READINESS_LEVELS } from "./roadmap-constants";

// ---------- Readiness Types ----------

export type ReadinessLevel = 1 | 2 | 3 | 4 | 5;

export interface ReadinessInfo {
    level: ReadinessLevel;
    emoji: string;
    label: string;
    description: string;
}

// ---------- Types ----------

export interface RoadmapDetailAction {
    id: number;
    action_type: string;
    title: string;
    description: string;
    source_url?: string | null;
    metadata_json?: Record<string, unknown>;
}

export type MappingSource = "actionkit_direct" | "rag" | "fallback";

export interface RoadmapDetailStep {
    id: number;
    title: string;
    status: string;
    completed_at?: string | null;
    detail?: {
        id: number;
        phase: string;
        objective: string;
        estimated_days: number;
        source_count?: number | null;
        has_fallback?: boolean | null;
        mapping_source?: MappingSource | null;
        actions: RoadmapDetailAction[];
    } | null;
}

export interface RoadmapDetailResponse {
    roadmap_id: string;
    title: string;
    created_at: string;
    steps: RoadmapDetailStep[];
}

export type PhaseState = "COMPLETED" | "CURRENT" | "LOCKED" | "FUTURE";

export type StepItemState = "DONE" | "ACTIVE" | "LOCKED";

export interface EnhancedPhaseGroup {
    phase: string;
    objective: string;
    steps: RoadmapDetailStep[];
    state: PhaseState;
    progress: number;
    completedAt: string | null;
    estimatedDays: number;
}

// ---------- Constants ----------

export const STATUS_LABEL: Record<string, string> = {
    PENDING: "대기",
    IN_PROGRESS: "진행 중",
    COMPLETED: "완료",
    BLOCKED: "보류",
};

export const ACTION_TYPE_LABEL: Record<string, string> = {
    CHECKLIST: "체크리스트",
    LEGAL_BASIS: "법적 근거",
    DOCUMENT: "필수 서류",
};

export const TOGGLE_ACTION_TYPES = new Set(["CHECKLIST", "DOCUMENT"]);

// ---------- Functions ----------

export function derivePhaseGroups(steps: RoadmapDetailStep[]): EnhancedPhaseGroup[] {
    const grouped = new Map<string, RoadmapDetailStep[]>();
    for (const step of steps) {
        const phase = step.detail?.phase || "기본";
        const bucket = grouped.get(phase) ?? [];
        bucket.push(step);
        grouped.set(phase, bucket);
    }

    const phases: EnhancedPhaseGroup[] = [];
    let foundCurrent = false;

    for (const [phase, phaseSteps] of grouped) {
        const completed = phaseSteps.filter((s) => s.status === "COMPLETED").length;
        const progress = phaseSteps.length ? Math.round((completed / phaseSteps.length) * 100) : 0;
        const allCompleted = completed === phaseSteps.length;
        const hasInProgress = phaseSteps.some((s) => s.status === "IN_PROGRESS");

        let state: PhaseState;
        if (allCompleted) {
            state = "COMPLETED";
        } else if (!foundCurrent && (hasInProgress || !allCompleted)) {
            state = "CURRENT";
            foundCurrent = true;
        } else if (foundCurrent) {
            state = phases.length > 0 && phases[phases.length - 1].state === "LOCKED" ? "FUTURE" : "LOCKED";
        } else {
            state = "LOCKED";
        }

        const lastCompletedStep = phaseSteps
            .filter((s) => s.completed_at)
            .sort((a, b) => (b.completed_at ?? "").localeCompare(a.completed_at ?? ""))
            [0];

        const objective = phaseSteps[0]?.detail?.objective || "";
        const estimatedDays = phaseSteps.reduce((sum, s) => sum + (s.detail?.estimated_days || 0), 0);

        phases.push({
            phase,
            objective,
            steps: phaseSteps,
            state,
            progress,
            completedAt: allCompleted ? (lastCompletedStep?.completed_at ?? null) : null,
            estimatedDays,
        });
    }

    return phases;
}

export function deriveStepItemState(
    step: RoadmapDetailStep,
    phaseState: PhaseState,
    isNextActionable?: boolean,
): StepItemState {
    if (step.status === "COMPLETED") return "DONE";
    if (phaseState === "CURRENT" && step.status === "IN_PROGRESS") return "ACTIVE";
    if (phaseState === "CURRENT" && step.status === "PENDING" && isNextActionable) return "ACTIVE";
    return "LOCKED";
}

export function computeDeadlineDate(
    createdAt: string,
    steps: RoadmapDetailStep[],
    targetStep?: RoadmapDetailStep,
): Date {
    const baseDate = new Date(createdAt);
    let totalDays = 0;

    for (const step of steps) {
        totalDays += step.detail?.estimated_days || 0;
        if (targetStep && step.id === targetStep.id) break;
    }

    const deadline = new Date(baseDate);
    deadline.setDate(deadline.getDate() + totalDays);
    return deadline;
}

export function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    return `${date.getFullYear()}.${String(date.getMonth() + 1).padStart(2, "0")}.${String(date.getDate()).padStart(2, "0")}`;
}

export function formatDeadlineDate(date: Date): { month: string; day: string; daysLeft: number } {
    const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const daysLeft = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return {
        month: months[date.getMonth()],
        day: String(date.getDate()).padStart(2, "0"),
        daysLeft,
    };
}

// ---------- Endowed Progress ----------

export function computeEndowedProgress(
    completedSteps: number,
    totalSteps: number,
): { display: number; actual: number; endowedSteps: number; totalWithEndowed: number } {
    const endowedSteps = ENDOWED_STEPS;
    const totalWithEndowed = totalSteps + endowedSteps;
    const completedWithEndowed = completedSteps + endowedSteps;
    return {
        display: Math.round((completedWithEndowed / totalWithEndowed) * 100),
        actual: totalSteps > 0 ? Math.round((completedSteps / totalSteps) * 100) : 0,
        endowedSteps,
        totalWithEndowed,
    };
}

// ---------- Readiness Level ----------

export function computeReadinessLevel(progressPercent: number): ReadinessInfo {
    if (progressPercent >= 90) return READINESS_LEVELS[4];
    if (progressPercent >= 65) return READINESS_LEVELS[3];
    if (progressPercent >= 35) return READINESS_LEVELS[2];
    if (progressPercent >= 10) return READINESS_LEVELS[1];
    return READINESS_LEVELS[0];
}
