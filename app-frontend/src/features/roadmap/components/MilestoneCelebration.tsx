"use client";

import { useEffect, useState, useCallback } from "react";
import { X, Trophy, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import { MILESTONE_INSIGHTS } from "./roadmap-constants";

function getRandomInsight(): string {
    const pool = MILESTONE_INSIGHTS.default ?? [];
    if (pool.length === 0) return "잘하고 계십니다!";
    return pool[Math.floor(Math.random() * pool.length)];
}

interface MilestoneCelebrationProps {
    type: "phase" | "step";
    phaseName?: string;
    previousReadiness?: string | null;
    currentReadiness?: string | null;
    onClose: () => void;
}

export function MilestoneCelebration({ type, phaseName, previousReadiness, currentReadiness, onClose }: MilestoneCelebrationProps) {
    const [visible, setVisible] = useState(false);
    const [insight] = useState(() => getRandomInsight());

    useEffect(() => {
        const timer = setTimeout(() => setVisible(true), 50);
        return () => clearTimeout(timer);
    }, []);

    // Phase celebration: trigger confetti
    useEffect(() => {
        if (type === "phase") {
            void (async () => {
                const confetti = (await import("canvas-confetti")).default;
                confetti({ particleCount: 100, spread: 70, origin: { y: 0.6 } });
            })();
        }
    }, [type]);

    // Step toast: auto-dismiss after 3 seconds
    useEffect(() => {
        if (type === "step") {
            const timer = setTimeout(() => {
                setVisible(false);
                setTimeout(onClose, 300);
            }, 3000);
            return () => clearTimeout(timer);
        }
    }, [type, onClose]);

    const handleClose = useCallback(() => {
        setVisible(false);
        setTimeout(onClose, 300);
    }, [onClose]);

    if (type === "step") {
        return (
            <div
                className={cn(
                    "fixed bottom-6 left-1/2 -translate-x-1/2 z-50 max-w-md w-full px-4 transition-all duration-300",
                    visible ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
                )}
            >
                <div className="bg-white rounded-xl shadow-lg border border-slate-200 px-4 py-3 flex items-center gap-3">
                    <Sparkles className="w-5 h-5 text-[#36a4f2] flex-shrink-0" />
                    <p className="text-sm text-slate-700 flex-grow">{insight}</p>
                    <button
                        type="button"
                        onClick={handleClose}
                        className="text-slate-400 hover:text-slate-600 flex-shrink-0"
                    >
                        <X className="w-4 h-4" />
                    </button>
                </div>
            </div>
        );
    }

    // Phase celebration modal
    return (
        <div
            className={cn(
                "fixed inset-0 z-50 flex items-center justify-center transition-all duration-300",
                visible ? "opacity-100" : "opacity-0",
            )}
        >
            <div className="absolute inset-0 bg-black/50" onClick={handleClose} role="presentation" />
            <div
                className={cn(
                    "relative bg-white rounded-2xl shadow-2xl max-w-md w-full mx-4 p-8 text-center transition-all duration-300",
                    visible ? "scale-100 translate-y-0" : "scale-95 translate-y-4",
                )}
            >
                <div className="w-16 h-16 bg-[#36a4f2]/10 rounded-full flex items-center justify-center mx-auto mb-4">
                    <Trophy className="w-8 h-8 text-[#36a4f2]" />
                </div>
                <h3 className="text-xl font-bold text-slate-900 mb-2">
                    {phaseName ? `'${phaseName}' 단계 완료!` : "단계 완료!"}
                </h3>
                {previousReadiness && currentReadiness && previousReadiness !== currentReadiness && (
                    <p className="text-sm font-medium text-[#36a4f2] mb-2">
                        {previousReadiness} → {currentReadiness}
                    </p>
                )}
                <p className="text-slate-600 text-sm mb-6">{insight}</p>
                <button
                    type="button"
                    onClick={handleClose}
                    className="px-6 py-2.5 bg-[#36a4f2] hover:bg-[#2b83c2] text-white text-sm font-medium rounded-lg shadow-sm shadow-[#36a4f2]/30 transition-all"
                >
                    계속하기
                </button>
            </div>
        </div>
    );
}
