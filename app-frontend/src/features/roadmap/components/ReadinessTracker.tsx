"use client";

import { READINESS_LEVELS } from "./roadmap-constants";
import { computeReadinessLevel } from "./roadmap-utils";

interface ReadinessTrackerProps {
    progressPercent: number;
}

export function ReadinessTracker({ progressPercent }: ReadinessTrackerProps) {
    const current = computeReadinessLevel(progressPercent);

    return (
        <div className="flex items-center gap-1 sm:gap-2 overflow-x-auto">
            {READINESS_LEVELS.map((level, idx) => {
                const isPast = level.level < current.level;
                const isCurrent = level.level === current.level;

                return (
                    <div key={level.level} className="flex items-center gap-1 sm:gap-2 shrink-0">
                        {idx > 0 && (
                            <div
                                className={`w-3 sm:w-5 h-px ${
                                    isPast || isCurrent ? "bg-[#36a4f2]" : "bg-slate-200 border-dashed"
                                }`}
                            />
                        )}
                        <div
                            className={`flex items-center gap-1 rounded-full px-2 py-1 text-[10px] sm:text-xs font-medium whitespace-nowrap ${
                                isCurrent
                                    ? "bg-[#36a4f2]/10 text-[#36a4f2] ring-1 ring-[#36a4f2]/30"
                                    : isPast
                                      ? "bg-slate-100 text-slate-400"
                                      : "bg-transparent text-slate-300"
                            }`}
                            title={level.description}
                        >
                            <span className="text-xs sm:text-sm">
                                {isCurrent ? level.emoji : isPast ? "✓" : "○"}
                            </span>
                            <span className="hidden sm:inline">{level.label}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
