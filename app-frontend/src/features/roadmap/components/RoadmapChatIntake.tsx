"use client";

import { useEffect, useMemo, useState } from "react";
import {
    Bot,
    Briefcase,
    CalendarClock,
    Database,
    Lightbulb,
    Loader2,
    MapPin,
    Paperclip,
    Sparkles,
    Wallet,
} from "lucide-react";
import { INTAKE_FIELD_SUGGESTIONS, VALIDATE_FALLBACK_MESSAGE } from "./roadmap-constants";

export interface RoadmapIntakePayload {
    business_type: string;
    location: string;
    description: string;
    startup_type: string;
    open_timeline: string;
    budget_range: string;
    additional_notes: string;
    goal_horizon_days: number;
    experience_level: string;
}

interface RoadmapChatIntakeProps {
    onValidate: (input: RoadmapRawInput) => Promise<RoadmapValidationResult>;
    onSubmit: (payload: RoadmapIntakePayload) => Promise<void>;
    onRefresh?: () => void;
    externalError?: string | null;
    isAuthenticated?: boolean;
    onRequireLogin?: () => void;
    isGenerating?: boolean;
    generatingStatus?: {
        status?: string;
        stage?: string;
        progress?: number;
    };
    onCancelGenerating?: () => void;
}

type FieldKey =
    | "business_type"
    | "location"
    | "startup_type"
    | "open_timeline"
    | "budget_range"
    | "description";

export interface RoadmapRawInput {
    business_type: string;
    location: string;
    startup_type: string;
    open_timeline: string;
    budget_range: string;
    description: string;
}

export interface RoadmapValidationResult {
    payload: RoadmapIntakePayload;
    summary: string;
}

const QUESTIONS: Array<{ key: FieldKey; prompt: string; required: boolean; label: string }> = [
    { key: "business_type", prompt: "어떤 업종으로 창업을 준비하시나요?", required: true, label: "업종" },
    { key: "location", prompt: "어느 지역에서 시작하시나요?", required: true, label: "지역" },
    { key: "startup_type", prompt: "창업 형태는 무엇인가요? (개인사업자/법인/미정)", required: true, label: "형태" },
    { key: "open_timeline", prompt: "오픈 목표 시점은 언제인가요? (예: 3개월 내)", required: true, label: "오픈" },
    { key: "budget_range", prompt: "초기 예산 범위는 어느 정도인가요?", required: true, label: "예산" },
    { key: "description", prompt: "추가로 고려 중인 조건이나 설명이 있나요? (선택)", required: false, label: "추가 설명" },
];


const PANEL_ROWS: Array<{ key: FieldKey; label: string; icon: React.ReactNode }> = [
    { key: "business_type", label: "업종", icon: <Briefcase className="h-3 w-3" /> },
    { key: "location", label: "지역", icon: <MapPin className="h-3 w-3" /> },
    { key: "startup_type", label: "형태", icon: <Database className="h-3 w-3" /> },
    { key: "open_timeline", label: "오픈", icon: <CalendarClock className="h-3 w-3" /> },
    { key: "budget_range", label: "예산", icon: <Wallet className="h-3 w-3" /> },
];

export const RoadmapChatIntake = ({
    onValidate,
    onSubmit,
    onRefresh,
    externalError,
    isAuthenticated = true,
    onRequireLogin,
    isGenerating = false,
    generatingStatus,
    onCancelGenerating,
}: RoadmapChatIntakeProps) => {
    const [stepIndex, setStepIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<FieldKey, string>>({
        business_type: "",
        location: "",
        startup_type: "",
        open_timeline: "",
        budget_range: "",
        description: "",
    });
    const [input, setInput] = useState("");
    const [validating, setValidating] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [validated, setValidated] = useState<RoadmapValidationResult | null>(null);

    const current = QUESTIONS[stepIndex];
    const isLast = stepIndex === QUESTIONS.length - 1;
    const requiredKeys = QUESTIONS.filter((q) => q.required).map((q) => q.key);

    const requiredCompleted = useMemo(
        () => requiredKeys.filter((key) => answers[key].trim().length > 0).length,
        [answers, requiredKeys]
    );
    const requiredMissing = requiredCompleted < requiredKeys.length;
    const progressPercent = Math.round((requiredCompleted / requiredKeys.length) * 100);

    useEffect(() => {
        if (!current) return;
        setInput(answers[current.key] || "");
    }, [current, answers]);

    const appendCurrentAnswer = () => {
        if (!current) return false;
        if (current.required && !input.trim()) {
            setError("필수 항목은 비워둘 수 없습니다.");
            return false;
        }
        setError(null);
        setAnswers((prev) => ({ ...prev, [current.key]: input.trim() }));
        return true;
    };

    const handleNext = () => {
        if (!isAuthenticated) {
            onRequireLogin?.();
            return;
        }
        if (!appendCurrentAnswer()) return;
        if (!isLast) {
            setStepIndex((prev) => prev + 1);
        }
    };

    const handleValidate = async () => {
        if (!isAuthenticated) {
            onRequireLogin?.();
            return;
        }
        if (!appendCurrentAnswer()) return;
        const rawInput: RoadmapRawInput = {
            business_type: (answers.business_type || (current?.key === "business_type" ? input : "")).trim(),
            location: (answers.location || (current?.key === "location" ? input : "")).trim(),
            startup_type: (answers.startup_type || (current?.key === "startup_type" ? input : "")).trim(),
            open_timeline: (answers.open_timeline || (current?.key === "open_timeline" ? input : "")).trim(),
            budget_range: (answers.budget_range || (current?.key === "budget_range" ? input : "")).trim(),
            description: (answers.description || (current?.key === "description" ? input : "")).trim(),
        };
        if (
            !rawInput.business_type
            || !rawInput.location
            || !rawInput.startup_type
            || !rawInput.open_timeline
            || !rawInput.budget_range
        ) {
            setError("업종, 지역, 창업 형태, 오픈 시점, 예산은 필수입니다.");
            return;
        }
        setValidating(true);
        setError(null);
        try {
            const result = await onValidate(rawInput);
            setValidated(result);
        } catch (e) {
            console.error(e);
            setError(VALIDATE_FALLBACK_MESSAGE);
        } finally {
            setValidating(false);
        }
    };

    const handleSubmit = async () => {
        if (!isAuthenticated) {
            onRequireLogin?.();
            return;
        }
        if (!validated) return;
        setSubmitting(true);
        setError(null);
        try {
            await onSubmit(validated.payload);
        } catch (e) {
            console.error(e);
            setError("생성 요청을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.");
            setSubmitting(false);
        }
    };

    const handleEdit = () => {
        setValidated(null);
        setError(null);
        setStepIndex(0);
    };

    const renderedHistory = QUESTIONS.slice(0, stepIndex)
        .filter((q) => answers[q.key])
        .map((q) => ({ prompt: q.prompt, answer: answers[q.key] || "(미입력)" }));

    const suggestionItems = validated ? [] : (INTAKE_FIELD_SUGGESTIONS[current.key] || []);

    return (
        <section className="overflow-hidden rounded-3xl border border-slate-200 bg-slate-50/60">
            <div className="border-b border-slate-200 bg-white/60 px-6 py-5 sm:px-8">
                <div className="flex items-end justify-between">
                    <span className="text-sm font-semibold text-slate-600">
                        1단계: 비즈니스 정보 수집 중
                    </span>
                    <span className="text-sm font-bold text-blue-600">{progressPercent}%</span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-slate-200">
                    <div
                        className="h-2 rounded-full bg-blue-600 transition-all duration-500"
                        style={{ width: `${Math.max(5, progressPercent)}%` }}
                    />
                </div>
            </div>

            <div className="grid gap-6 p-6 sm:p-8 lg:grid-cols-[1fr_280px]">
                <div className="flex min-h-[520px] flex-col">
                    <div className="hide-scrollbar flex-1 space-y-5 overflow-y-auto pr-2">
                        <div className="flex items-start gap-3">
                            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                                <Bot className="h-5 w-5" />
                            </div>
                            <div className="max-w-[85%]">
                                <p className="ml-1 text-xs font-semibold text-slate-500">StepZero AI</p>
                                <div className="mt-1 rounded-xl rounded-tl-none border border-slate-200 bg-white p-4 text-sm leading-relaxed text-slate-700 shadow-sm">
                                    {validated
                                        ? "정보 검증이 완료되었습니다. 아래 내용을 확인한 뒤 로드맵 생성을 시작하세요."
                                        : current.prompt}
                                </div>
                            </div>
                        </div>

                        {renderedHistory.map((item, idx) => (
                            <div key={`${item.prompt}-${idx}`} className="space-y-1">
                                <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-xs font-medium text-blue-700">
                                    {item.prompt}
                                </p>
                                <p className="ml-auto w-fit rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 shadow-sm">
                                    {item.answer}
                                </p>
                            </div>
                        ))}

                        {validated ? (
                            <div className="ml-auto w-fit max-w-[90%] rounded-lg border border-emerald-200 bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                                {validated.summary}
                            </div>
                        ) : suggestionItems.length ? (
                            <div className="ml-12 flex flex-wrap gap-2">
                                {suggestionItems.map((chip) => (
                                    <button
                                        key={chip}
                                        type="button"
                                        onClick={() => setInput(chip)}
                                        className="rounded-full border border-slate-200 bg-white px-3 py-1 text-xs font-medium text-slate-600 hover:border-blue-300 hover:text-blue-700"
                                    >
                                        {chip}
                                    </button>
                                ))}
                            </div>
                        ) : null}

                        {isGenerating ? (
                            <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4">
                                <div className="flex items-center gap-2 text-sm font-semibold text-blue-700">
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                    로드맵 생성 진행 중
                                </div>
                                <div className="mt-2 text-xs text-slate-600">
                                    상태: <span className="font-semibold">{generatingStatus?.status || "RUNNING"}</span> / 단계:{" "}
                                    <span className="font-semibold">{generatingStatus?.stage || "DETAIL_GENERATING"}</span> / 진행률:{" "}
                                    <span className="font-semibold">{generatingStatus?.progress ?? 0}%</span>
                                </div>
                                <div className="mt-3 h-2 rounded-full bg-slate-200">
                                    <div
                                        className="h-2 rounded-full bg-blue-500 transition-all"
                                        style={{ width: `${Math.min(Math.max(generatingStatus?.progress ?? 0, 0), 100)}%` }}
                                    />
                                </div>
                                {onCancelGenerating ? (
                                    <button
                                        type="button"
                                        onClick={onCancelGenerating}
                                        className="mt-3 rounded-lg border border-slate-300 bg-white px-3 py-1 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                                    >
                                        생성 상태 숨기기
                                    </button>
                                ) : null}
                            </div>
                        ) : null}

                        {error ? <p className="text-sm text-red-600">{error}</p> : null}
                        {externalError ? <p className="text-sm text-red-600">{externalError}</p> : null}
                    </div>

                    <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm">
                        <div className="flex items-center gap-2">
                            <button
                                type="button"
                                className="rounded-lg p-2 text-slate-400 hover:bg-slate-100"
                            >
                                <Paperclip className="h-4 w-4" />
                            </button>
                            <input
                                value={input}
                                onChange={(e) => {
                                    if (!isAuthenticated) {
                                        onRequireLogin?.();
                                        return;
                                    }
                                    setInput(e.target.value);
                                }}
                                onFocus={() => {
                                    if (!isAuthenticated) onRequireLogin?.();
                                }}
                                placeholder={current.required ? "여기에 답변을 입력하세요..." : "선택 정보를 입력하세요..."}
                                disabled={isGenerating || validating || submitting}
                                className="flex-1 border-none bg-transparent px-2 py-2 text-sm outline-none placeholder:text-slate-400 disabled:bg-slate-100"
                            />
                            {validated ? (
                                <>
                                    <button
                                        type="button"
                                        onClick={handleEdit}
                                        disabled={submitting || isGenerating}
                                        className="rounded-lg border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                                    >
                                        수정
                                    </button>
                                    <button
                                        type="button"
                                        onClick={() => void handleSubmit()}
                                        disabled={submitting || isGenerating}
                                        className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                                    >
                                        <Sparkles className="h-3 w-3" />
                                        {submitting || isGenerating ? "생성 중..." : "로드맵 생성"}
                                    </button>
                                </>
                            ) : !isLast ? (
                                <button
                                    type="button"
                                    onClick={handleNext}
                                    disabled={submitting || validating || isGenerating}
                                    className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                                >
                                    <Sparkles className="h-3 w-3" />
                                    다음 질문
                                </button>
                            ) : (
                                <button
                                    type="button"
                                    onClick={() => void handleValidate()}
                                    disabled={submitting || validating || requiredMissing || isGenerating}
                                    className="inline-flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-xs font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                                >
                                    <Sparkles className="h-3 w-3" />
                                    {validating ? "검증 중..." : "정보 검증"}
                                </button>
                            )}
                        </div>
                        <p className="py-2 text-center text-[11px] text-slate-400">
                            StepZero AI는 비즈니스 로직을 학습하며 답변을 생성합니다.
                        </p>
                    </div>
                </div>

                <aside className="space-y-4">
                    <section className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                        <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-slate-800">
                            <Database className="h-4 w-4 text-blue-600" />
                            수집된 정보
                        </h3>
                        <ul className="space-y-2">
                            {PANEL_ROWS.map((row) => (
                                <li key={row.key} className="flex items-center justify-between">
                                    <span className="inline-flex items-center gap-1 text-xs text-slate-500">
                                        {row.icon}
                                        {row.label}
                                    </span>
                                    <span className="rounded bg-slate-100 px-2 py-0.5 text-xs font-semibold text-slate-700">
                                        {answers[row.key] || "-"}
                                    </span>
                                </li>
                            ))}
                        </ul>
                    </section>

                    <section className="rounded-2xl border border-blue-100 bg-blue-50/40 p-4 shadow-sm">
                        <h3 className="mb-3 flex items-center gap-2 text-sm font-bold text-blue-700">
                            <Lightbulb className="h-4 w-4" />
                            AI 가이드 팁
                        </h3>
                        <ul className="space-y-2 text-xs text-slate-600">
                            <li>• 구체적일수록 더 정확한 로드맵이 생성됩니다.</li>
                            <li>• 타겟 고객/예산/일정을 함께 입력하면 정확도가 올라갑니다.</li>
                            <li>• 필수 정보가 채워지면 검증 후 생성으로 이동합니다.</li>
                        </ul>
                    </section>

                    <div className="flex items-center gap-2">
                        <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${requiredMissing ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                            {requiredMissing ? "필수값 미완료" : "필수값 완료"}
                        </span>
                        {onRefresh ? (
                            <button
                                type="button"
                                onClick={onRefresh}
                                disabled={submitting || validating}
                                className="rounded-full border border-slate-300 bg-white px-2 py-1 text-[11px] font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-50"
                            >
                                상태 새로고침
                            </button>
                        ) : null}
                    </div>
                </aside>
            </div>
        </section>
    );
};
