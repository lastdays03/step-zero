"use client";

import { useEffect, useMemo, useState } from 'react';
import { apiClient } from "@/lib/api-client";
import { useDashboard } from '../hooks/useDashboard';
import { ProgressCard } from './ProgressCard';
import { RoadmapStepper } from './RoadmapStepper';
import { GrowthClubCard } from './GrowthClubCard';
import { computeEndowedProgress, computeReadinessLevel } from '@/features/roadmap/components';
import { fetchRoadmapDetail } from '@/features/roadmap/api';
import { ColdStartHero } from './ColdStartHero';
import { Card, CardContent } from "@/components/ui/card";
import { Clock, CheckSquare } from 'lucide-react';
import type { RoadmapDetailResponse } from '@/features/roadmap/components/RoadmapExecutionView';

const ACTIVE_ROADMAP_STORAGE_KEY = "stepzero_active_roadmap_id";

export const DashboardView = () => {
    const [activeRoadmapId] = useState<string | null>(() => {
        if (typeof window === "undefined") return null;
        return localStorage.getItem(ACTIVE_ROADMAP_STORAGE_KEY);
    });

    const { data, loading: isLoading } = useDashboard(activeRoadmapId);
    const [roadmapDetail, setRoadmapDetail] = useState<RoadmapDetailResponse | null>(null);
    const [documentsLoading, setDocumentsLoading] = useState(false);
    const [documentsError, setDocumentsError] = useState<string | null>(null);

    const isRoadmapNotReady =
        !data ||
        data.current_phase.status === "GUEST" ||
        data.current_phase.status === "READY" ||
        data.roadmap.length === 0;
    const dashboardPhaseTitle = data?.current_phase.title?.trim();

    useEffect(() => {
        if (isRoadmapNotReady) {
            setRoadmapDetail(null);
            setDocumentsError(null);
            setDocumentsLoading(false);
            return;
        }

        let cancelled = false;
        const loadRoadmapDetail = async () => {
            setDocumentsLoading(true);
            setDocumentsError(null);
            try {
                let detail: RoadmapDetailResponse;
                if (activeRoadmapId) {
                    detail = await fetchRoadmapDetail(activeRoadmapId);
                } else {
                    const response = await apiClient.get<RoadmapDetailResponse>("/roadmaps/latest/detail");
                    detail = response.data;
                }
                if (!cancelled) {
                    setRoadmapDetail(detail);
                }
            } catch (e) {
                console.error("Failed to load roadmap documents", e);
                if (!cancelled) {
                    setDocumentsError("필요 서류를 불러오지 못했습니다.");
                    setRoadmapDetail(null);
                }
            } finally {
                if (!cancelled) {
                    setDocumentsLoading(false);
                }
            }
        };

        void loadRoadmapDetail();

        return () => {
            cancelled = true;
        };
    }, [isRoadmapNotReady, activeRoadmapId]);

    const currentStep = useMemo(() => {
        if (!roadmapDetail) return null;
        return (
            roadmapDetail.steps.find(
                (step) =>
                    dashboardPhaseTitle
                    && (step.detail?.phase === dashboardPhaseTitle || step.title === dashboardPhaseTitle)
            )
            || roadmapDetail.steps.find((step) => step.status === "IN_PROGRESS")
            || roadmapDetail.steps.find((step) => step.status === "PENDING")
            || roadmapDetail.steps.find((step) => step.status !== "COMPLETED")
            || roadmapDetail.steps[0]
            || null
        );
    }, [roadmapDetail, dashboardPhaseTitle]);

    const nextRoadmapTitle = useMemo(() => {
        if (!roadmapDetail || !currentStep) {
            const currentRoadmapIndex = data?.roadmap.findIndex((step) => step.status === "current") ?? -1;
            return currentRoadmapIndex >= 0 && data?.roadmap[currentRoadmapIndex + 1]
                ? data.roadmap[currentRoadmapIndex + 1].title
                : null;
        }
        const currentIndex = roadmapDetail.steps.findIndex((step) => step.id === currentStep.id);
        if (currentIndex < 0) return null;
        const nextStep = roadmapDetail.steps
            .slice(currentIndex + 1)
            .find((step) => step.status !== "COMPLETED");
        return nextStep?.title || null;
    }, [roadmapDetail, currentStep, data?.roadmap]);

    const endowedProgress = useMemo(() => {
        if (!roadmapDetail) return null;
        const completed = roadmapDetail.steps.filter((s) => s.status === "COMPLETED").length;
        return computeEndowedProgress(completed, roadmapDetail.steps.length);
    }, [roadmapDetail]);

    const readinessInfo = useMemo(() => {
        if (!endowedProgress) return null;
        return computeReadinessLevel(endowedProgress.display);
    }, [endowedProgress]);

    const readinessLabel = readinessInfo ? `${readinessInfo.emoji} ${readinessInfo.label}` : null;

    const [upgradeAlert, setUpgradeAlert] = useState<{ from: string; to: string } | null>(null);

    useEffect(() => {
        if (!readinessInfo || !activeRoadmapId) return;
        const storageKey = `stepzero_readiness_level_${activeRoadmapId}`;
        const stored = localStorage.getItem(storageKey);
        const storedLevel = stored ? Number(stored) : 0;
        if (storedLevel > 0 && readinessInfo.level > storedLevel) {
            const prevInfo = computeReadinessLevel(
                storedLevel === 1 ? 0 : storedLevel === 2 ? 10 : storedLevel === 3 ? 35 : storedLevel === 4 ? 65 : 90,
            );
            setUpgradeAlert({ from: prevInfo.label, to: readinessInfo.label });
            const timer = setTimeout(() => setUpgradeAlert(null), 5000);
            localStorage.setItem(storageKey, String(readinessInfo.level));
            return () => clearTimeout(timer);
        }
        localStorage.setItem(storageKey, String(readinessInfo.level));
    }, [readinessInfo, activeRoadmapId]);

    const documentActions = useMemo(() => {
        if (!currentStep) return [];

        return ((currentStep.detail?.actions || []) as Array<{
            id: number;
            title: string;
            description: string;
            source_url?: string | null;
            metadata_json?: Record<string, unknown>;
            action_type: string;
        }>)
            .filter((action) => action.action_type === "DOCUMENT")
            .map((doc) => {
                const meta = (doc.metadata_json || {}) as Record<string, unknown>;
                const apiUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ?? "";
                const actionkitItemId = meta.actionkit_item_id as number | undefined;

                let viewUrl: string | null = null;
                if (actionkitItemId) {
                    viewUrl = `${apiUrl}/api/v1/actionkits/items/${actionkitItemId}/view`;
                } else {
                    const raw =
                        (typeof meta.download_url === "string" && meta.download_url)
                        || (typeof meta.file_url === "string" && meta.file_url)
                        || (typeof meta.template_url === "string" && meta.template_url)
                        || (typeof meta.source_url === "string" && meta.source_url)
                        || doc.source_url
                        || null;
                    if (raw) {
                        const itemMatch = raw.match(/\/actionkits\/items\/(\d+)$/);
                        viewUrl = itemMatch ? `${raw}/view` : raw;
                    }
                }

                return {
                    id: doc.id,
                    title: doc.title,
                    description: doc.description,
                    completed: doc.metadata_json?.completed === true,
                    stepTitle: currentStep.title,
                    viewUrl,
                };
            });
    }, [currentStep]);

    if (isLoading || !data) {
        return <div className="p-8 text-center">Loading...</div>;
    }

    if (isRoadmapNotReady) {
        return <ColdStartHero />;
    }

    return (
        <div className="">
            {upgradeAlert && (
                <div className="mb-4 flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700 shadow-sm">
                    <span>🎉 준비도가 &lsquo;{upgradeAlert.from}&rsquo; → &lsquo;{upgradeAlert.to}&rsquo;로 올라갔습니다!</span>
                    <button
                        type="button"
                        onClick={() => setUpgradeAlert(null)}
                        className="ml-3 text-emerald-400 hover:text-emerald-600"
                    >
                        ✕
                    </button>
                </div>
            )}
            {/* Main Grid: 4 Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

                {/* 1. Progress Card (Span 3) */}
                <div className="md:col-span-3 lg:col-span-3 h-full">
                    <ProgressCard
                        phase={data.current_phase}
                        daysLeft={data.stats.days_left}
                        nextTitle={nextRoadmapTitle}
                        endowedProgress={endowedProgress?.display ?? null}
                        readinessLabel={readinessLabel}
                    />
                </div>

                {/* 2. Growth Club (Span 1) */}
                <div className="md:col-span-1 lg:col-span-1 h-full">
                    <GrowthClubCard onlineCount={data.growth_club.founders_online} />
                </div>

                {/* 3. Roadmap (Full Span 4) */}
                <div className="md:col-span-3 lg:col-span-4">
                    <RoadmapStepper steps={data.roadmap} />
                </div>

                {/* 4. Action Kit / Documents (Span 2) */}
                <Card className="md:col-span-2 lg:col-span-2 bg-white/90 backdrop-blur-sm border border-white/50 rounded-3xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)]">
                    <CardContent className="p-8">
                        <h3 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
                            <span className="w-1 h-5 bg-[#36a4f2] rounded-full"></span>
                            필요 서류
                        </h3>
                        <div className="space-y-3">
                            {documentsLoading ? (
                                <p className="text-sm text-slate-400 text-center py-4">필요 서류를 불러오는 중입니다...</p>
                            ) : documentsError ? (
                                <p className="text-sm text-red-500 text-center py-4">{documentsError}</p>
                            ) : documentActions.length === 0 ? (
                                <p className="text-sm text-slate-400 text-center py-4">현재 단계에서 필요한 서류가 없습니다.</p>
                            ) : (
                                documentActions.slice(0, 6).map((doc) => (
                                    <div
                                        key={doc.id}
                                        className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2"
                                    >
                                        <div className="flex items-start justify-between gap-2">
                                            <div>
                                                <p className="text-sm font-semibold text-slate-800">{doc.title}</p>
                                                <p className="mt-0.5 text-[11px] text-slate-500">{doc.stepTitle}</p>
                                            </div>
                                            <span
                                                className={`rounded-full px-2 py-0.5 text-[10px] font-bold ${
                                                    doc.completed
                                                        ? "bg-emerald-100 text-emerald-700"
                                                        : "bg-amber-100 text-amber-700"
                                                }`}
                                            >
                                                {doc.completed ? "완료" : "필수"}
                                            </span>
                                        </div>
                                        {doc.description ? (
                                            <p className="mt-1 text-xs text-slate-600 line-clamp-2">{doc.description}</p>
                                        ) : null}
                                        <div className="mt-2">
                                            {doc.viewUrl ? (
                                                <a
                                                    href={doc.viewUrl}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="inline-flex rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-semibold text-blue-700 hover:bg-blue-100"
                                                >
                                                    문서 보기
                                                </a>
                                            ) : (
                                                <span className="text-[11px] text-slate-400">
                                                    문서 링크 없음
                                                </span>
                                            )}
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* 5. Stat Card 1: Timer (Span 1) */}
                <Card className="md:col-span-1 lg:col-span-1 bg-white/90 backdrop-blur-sm border border-white/50 rounded-3xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] text-center">
                    <CardContent className="p-8 flex flex-col justify-center items-center h-full">
                        <div className="w-12 h-12 rounded-full bg-orange-100 text-orange-500 flex items-center justify-center mb-4">
                            <Clock className="w-6 h-6" />
                        </div>
                        <h4 className="text-2xl font-black text-slate-800">{data.stats.days_left}일</h4>
                        <p className="text-xs font-bold text-slate-500 mt-1 uppercase">마감일까지 남은 기간</p>
                    </CardContent>
                </Card>

                {/* 6. Stat Card 2: Tasks (Span 1) */}
                <Card className="md:col-span-1 lg:col-span-1 bg-white/90 backdrop-blur-sm border border-white/50 rounded-3xl shadow-[0_4px_20px_-2px_rgba(0,0,0,0.05)] text-center">
                    <CardContent className="p-8 flex flex-col justify-center items-center h-full">
                        <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-500 flex items-center justify-center mb-4">
                            <CheckSquare className="w-6 h-6" />
                        </div>
                        <h4 className="text-2xl font-black text-slate-800">{data.stats.tasks_completed}/{data.stats.total_tasks}</h4>
                        <p className="text-xs font-bold text-slate-500 mt-1 uppercase">작업 완료율</p>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};
