"use client";

import { useMemo, useState } from "react";

export interface RoadmapIntakePayload {
    business_type: string;
    location: string;
    description: string;
    goal_horizon_days: number;
    experience_level: string;
}

interface RoadmapChatIntakeProps {
    onSubmit: (payload: RoadmapIntakePayload) => Promise<void>;
    onCancel: () => void;
    externalError?: string | null;
}

type FieldKey = "business_type" | "location" | "description";

const QUESTIONS: Array<{ key: FieldKey; prompt: string; required: boolean }> = [
    { key: "business_type", prompt: "어떤 업종으로 창업을 준비하시나요?", required: true },
    { key: "location", prompt: "어느 지역에서 시작하시나요?", required: true },
    { key: "description", prompt: "추가로 고려 중인 조건이나 설명이 있나요? (선택)", required: false },
];

export const RoadmapChatIntake = ({ onSubmit, onCancel, externalError }: RoadmapChatIntakeProps) => {
    const [stepIndex, setStepIndex] = useState(0);
    const [answers, setAnswers] = useState<Record<FieldKey, string>>({
        business_type: "",
        location: "",
        description: "",
    });
    const [input, setInput] = useState("");
    const [submitting, setSubmitting] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const current = QUESTIONS[stepIndex];
    const isLast = stepIndex === QUESTIONS.length - 1;

    const requiredMissing = useMemo(() => {
        return !answers.business_type.trim() || !answers.location.trim();
    }, [answers.business_type, answers.location]);

    const appendCurrentAnswer = () => {
        if (!current) return;
        if (current.required && !input.trim()) {
            setError("필수 항목은 비워둘 수 없습니다.");
            return false;
        }
        setError(null);
        setAnswers((prev) => ({ ...prev, [current.key]: input.trim() }));
        setInput("");
        return true;
    };

    const handleNext = () => {
        if (!appendCurrentAnswer()) return;
        if (!isLast) {
            setStepIndex((prev) => prev + 1);
        }
    };

    const handleSubmit = async () => {
        if (!appendCurrentAnswer()) return;
        const payload: RoadmapIntakePayload = {
            business_type: (answers.business_type || (current?.key === "business_type" ? input : "")).trim(),
            location: (answers.location || (current?.key === "location" ? input : "")).trim(),
            description: (answers.description || (current?.key === "description" ? input : "")).trim(),
            goal_horizon_days: 30,
            experience_level: "BEGINNER",
        };
        if (!payload.business_type || !payload.location) {
            setError("업종과 지역은 필수입니다.");
            return;
        }
        setSubmitting(true);
        setError(null);
        try {
            await onSubmit(payload);
        } catch (e) {
            console.error(e);
            setError("생성 요청을 시작하지 못했습니다. 잠시 후 다시 시도해 주세요.");
            setSubmitting(false);
        }
    };

    const renderedHistory = QUESTIONS.slice(0, stepIndex).map((q) => ({
        prompt: q.prompt,
        answer: answers[q.key] || "(미입력)",
    }));

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
            <h2 className="text-xl font-bold text-slate-900">로드맵 생성을 위한 질문</h2>
            <p className="mt-1 text-sm text-slate-600">필수 정보(업종/지역)가 모두 입력되어야 생성이 시작됩니다.</p>

            <div className="mt-6 space-y-4 rounded-xl border border-slate-100 bg-slate-50 p-4">
                {renderedHistory.map((item, idx) => (
                    <div key={`${item.prompt}-${idx}`} className="space-y-2">
                        <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-sm text-blue-700">{item.prompt}</p>
                        <p className="ml-auto w-fit rounded-lg bg-white px-3 py-2 text-sm text-slate-800 shadow-sm">
                            {item.answer}
                        </p>
                    </div>
                ))}

                <div className="space-y-2">
                    <p className="inline-flex rounded-lg bg-blue-100 px-3 py-2 text-sm text-blue-700">{current.prompt}</p>
                    <input
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        placeholder={current.required ? "필수 입력" : "선택 입력"}
                        className="w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none focus:border-blue-400"
                    />
                </div>
            </div>

            <div className="mt-4 flex flex-wrap items-center gap-2">
                <span className={`rounded-full px-2 py-1 text-xs font-semibold ${requiredMissing ? "bg-amber-100 text-amber-700" : "bg-emerald-100 text-emerald-700"}`}>
                    {requiredMissing ? "필수값 미완료" : "필수값 완료"}
                </span>
            </div>

            {error ? <p className="mt-3 text-sm text-red-600">{error}</p> : null}
            {externalError ? <p className="mt-2 text-sm text-red-600">{externalError}</p> : null}

            <div className="mt-6 flex gap-3">
                <button
                    type="button"
                    onClick={onCancel}
                    disabled={submitting}
                    className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50"
                >
                    취소
                </button>
                {!isLast ? (
                    <button
                        type="button"
                        onClick={handleNext}
                        disabled={submitting}
                        className="rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-50"
                    >
                        다음 질문
                    </button>
                ) : (
                    <button
                        type="button"
                        onClick={() => void handleSubmit()}
                        disabled={submitting || requiredMissing}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-50"
                    >
                        {submitting ? "생성 요청 중..." : "로드맵 생성 시작"}
                    </button>
                )}
            </div>
        </section>
    );
};
