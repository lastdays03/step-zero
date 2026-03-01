import { useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";
import { STAGE_MESSAGES, GENERATING_INSIGHTS } from "./roadmap-constants";

interface RoadmapGeneratingStateProps {
    onCancel: () => void;
    status?: string;
    stage?: string;
    progress?: number;
    errorMessage?: string | null;
}

export const RoadmapGeneratingState = ({
    onCancel,
    status = "RUNNING",
    stage = "DETAIL_GENERATING",
    progress = 0,
    errorMessage,
}: RoadmapGeneratingStateProps) => {
    const [insightIndex, setInsightIndex] = useState(0);
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const interval = setInterval(() => {
            setVisible(false);
            setTimeout(() => {
                setInsightIndex((prev) => (prev + 1) % GENERATING_INSIGHTS.length);
                setVisible(true);
            }, 500);
        }, 5000);
        return () => clearInterval(interval);
    }, []);

    const stageMessage = STAGE_MESSAGES[stage] ?? STAGE_MESSAGES["DETAIL_GENERATING"];

    return (
        <section className="relative overflow-hidden rounded-3xl border border-blue-100 bg-white px-4 py-12 sm:px-6">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.12),transparent_45%),radial-gradient(circle_at_bottom_right,rgba(99,102,241,0.12),transparent_45%)]" />
            <div className="relative mx-auto flex max-w-2xl flex-col items-center text-center">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 text-blue-600">
                    <Loader2 className="h-7 w-7 animate-spin" />
                </div>
                <h2 className="mt-5 text-2xl font-extrabold text-slate-900">로드맵 생성 중입니다</h2>
                <p className="mt-3 text-sm text-slate-600 sm:text-base">
                    {stageMessage}
                    <br />
                    다른 화면으로 이동해도 생성은 계속 진행됩니다.
                </p>

                <div className="mt-4 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs text-slate-600">
                    상태: <span className="font-semibold text-slate-900">{status}</span> / 단계:{" "}
                    <span className="font-semibold text-slate-900">{stage}</span> / 진행률:{" "}
                    <span className="font-semibold text-slate-900">{progress}%</span>
                </div>

                <div className="mt-6 w-full rounded-2xl border border-slate-200 bg-slate-50 p-4 text-left">
                    <p className="text-xs font-semibold text-slate-500">현재 작업</p>
                    <div className="mt-2 flex items-center gap-2 text-sm text-slate-700">
                        <Sparkles className="h-4 w-4 text-blue-500 flex-shrink-0" />
                        <span>{stageMessage}</span>
                    </div>
                </div>

                <div className="mt-4 w-full rounded-xl border border-amber-100 bg-amber-50/60 p-3 text-left">
                    <p
                        className={`text-sm text-amber-800 transition-opacity duration-500 ${
                            visible ? "opacity-100" : "opacity-0"
                        }`}
                    >
                        {GENERATING_INSIGHTS[insightIndex]}
                    </p>
                </div>

                {errorMessage ? (
                    <p className="mt-4 text-sm font-medium text-red-600">{errorMessage}</p>
                ) : null}

                <button
                    type="button"
                    onClick={onCancel}
                    className="mt-6 rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                >
                    생성 화면 닫기
                </button>
            </div>
        </section>
    );
};
