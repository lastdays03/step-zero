"use client";

import { useEffect, useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

export interface RoadmapIntakePayload {
    business_type: string;
    location: string;
    description: string;
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

const QUESTIONS: Array<{ key: FieldKey; prompt: string; required: boolean }> = [
    { key: "business_type", prompt: "어떤 업종으로 창업을 준비하시나요?", required: true },
    { key: "location", prompt: "어느 지역에서 시작하시나요?", required: true },
    { key: "startup_type", prompt: "창업 형태는 무엇인가요? (개인사업자/법인/미정)", required: true },
    { key: "open_timeline", prompt: "오픈 목표 시점은 언제인가요? (예: 3개월 내)", required: true },
    { key: "budget_range", prompt: "초기 예산 범위는 어느 정도인가요?", required: true },
    { key: "description", prompt: "추가로 고려 중인 조건이나 설명이 있나요? (선택)", required: false },
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

    const requiredMissing = useMemo(() => {
        return (
            !answers.business_type.trim()
            || !answers.location.trim()
            || !answers.startup_type.trim()
            || !answers.open_timeline.trim()
            || !answers.budget_range.trim()
        );
    }, [
        answers.business_type,
        answers.location,
        answers.startup_type,
        answers.open_timeline,
        answers.budget_range,
    ]);

    useEffect(() => {
        if (!current) return;
        setInput(answers[current.key] || "");
    }, [current, answers]);

    const appendCurrentAnswer = () => {
        if (!current) return;
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
            setError("입력 검증에 실패했습니다. 업종/지역 정보를 다시 확인해 주세요.");
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

    const renderedHistory = QUESTIONS.slice(0, stepIndex).map((q) => ({
        prompt: q.prompt,
        answer: answers[q.key] || "(미입력)",
    }));

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
            <h2 className="text-xl font-bold text-slate-900">AI 로드맵 생성 채팅</h2>
            <p className="mt-1 text-sm text-slate-600">
                채팅으로 정보를 수집하고 검증한 뒤, 확인을 거쳐 로드맵 생성을 시작합니다.
            </p>

            <div className="mt-6 space-y-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
                {renderedHistory.map((item, idx) => (
                    <div key={`${item.prompt}-${idx}`} className="space-y-2">
                        <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-sm text-blue-700">{item.prompt}</p>
                        <p className="ml-auto w-fit rounded-lg bg-white px-3 py-2 text-sm text-slate-800 shadow-sm">
                            {item.answer}
                        </p>
                    </div>
                ))}

                {validated ? (
                    <div className="space-y-2">
                        <p className="inline-flex rounded-lg bg-emerald-100 px-3 py-2 text-sm text-emerald-700">
                            정보 검증이 완료되었습니다.
                        </p>
                        <p className="ml-auto w-fit rounded-lg bg-white px-3 py-2 text-sm text-slate-800 shadow-sm">
                            {validated.summary}
                        </p>
                        <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-sm text-blue-700">
                            위 정보로 로드맵 생성을 진행할까요?
                        </p>
                    </div>
                ) : (
                    <div className="space-y-2">
                        <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-sm text-blue-700">{current.prompt}</p>
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
                                if (!isAuthenticated) {
                                    onRequireLogin?.();
                                }
                            }}
                            placeholder={current.required ? "필수 입력" : "선택 입력"}
                            disabled={isGenerating || validating || submitting}
                            className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-400 disabled:bg-slate-100"
                        />
                    </div>
                )}
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ${requiredMissing ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                    {requiredMissing ? "필수값 미완료" : "필수값 완료"}
                </span>
            </div>

            {isGenerating ? (
                <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50/50 p-4">
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
                            className="h-full rounded-full bg-blue-500 transition-all"
                            style={{ width: `${Math.min(Math.max(generatingStatus?.progress ?? 0, 0), 100)}%` }}
                        />
                    </div>
                    <p className="mt-2 text-xs text-slate-500">
                        다른 화면으로 이동해도 생성은 계속 진행됩니다.
                    </p>
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

            {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
            {externalError ? <p className="mt-2 text-sm text-red-600">{externalError}</p> : null}

            <div className="mt-6 flex gap-3">
                {validated ? (
                    <>
                        <button
                            type="button"
                            onClick={handleEdit}
                            disabled={submitting || isGenerating}
                            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                        >
                            정보 수정
                        </button>
                        <button
                            type="button"
                            onClick={() => void handleSubmit()}
                            disabled={submitting || isGenerating}
                            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                        >
                            {submitting || isGenerating ? "생성 요청 중..." : "로드맵 생성 시작"}
                        </button>
                    </>
                ) : !isLast ? (
                    <button
                        type="button"
                        onClick={handleNext}
                        disabled={submitting || validating || isGenerating}
                        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                    >
                        다음 질문
                    </button>
                ) : (
                    <button
                        type="button"
                        onClick={() => void handleValidate()}
                        disabled={submitting || validating || requiredMissing || isGenerating}
                        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                    >
                        {validating ? "AI 검증 중..." : "정보 검증하기"}
                    </button>
                )}
                {onRefresh ? (
                    <button
                        type="button"
                        onClick={onRefresh}
                        disabled={submitting || validating}
                        className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                    >
                        상태 새로고침
                    </button>
                ) : null}
            </div>

            <div className="mt-4 text-xs text-slate-500">
                <span className="inline-flex items-center gap-1">
                    <Sparkles className="h-3 w-3 text-blue-500" />
                    필수 정보: 업종, 지역, 창업 형태, 오픈 시점, 예산
                </span>
            </div>
        </section>
    );
};
