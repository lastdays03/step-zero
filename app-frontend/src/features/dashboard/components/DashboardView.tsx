"use client";

import React, { useEffect, useMemo, useState } from 'react';
import { apiClient } from "@/lib/api-client";
import { useDashboard } from '../hooks/useDashboard';
import { ProgressCard } from './ProgressCard';
import { RoadmapStepper } from './RoadmapStepper';
import { GrowthClubCard } from './GrowthClubCard';
import { RoadmapGenerationPanel } from '@/features/roadmap/components';
import { useAuth } from "@/providers/AuthProvider";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Clock, CheckSquare } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import type { RoadmapDetailResponse } from '@/features/roadmap/components/RoadmapExecutionView';

export const DashboardView = () => {
    const { isLoggedIn } = useAuth();
    const { data, loading: isLoading, reload } = useDashboard();
    const [roadmapDetail, setRoadmapDetail] = useState<RoadmapDetailResponse | null>(null);
    const [documentsLoading, setDocumentsLoading] = useState(false);
    const [documentsError, setDocumentsError] = useState<string | null>(null);
    const [isLegalModalOpen, setIsLegalModalOpen] = useState(false);
    const [legalQuestion, setLegalQuestion] = useState("");
    const [legalAnswer, setLegalAnswer] = useState<string | null>(null);
    const [legalError, setLegalError] = useState<string | null>(null);
    const [legalLoading, setLegalLoading] = useState(false);

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
        const loadLatestRoadmapDetail = async () => {
            setDocumentsLoading(true);
            setDocumentsError(null);
            try {
                const response = await apiClient.get<RoadmapDetailResponse>("/roadmaps/latest/detail");
                if (!cancelled) {
                    setRoadmapDetail(response.data);
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

        void loadLatestRoadmapDetail();

        return () => {
            cancelled = true;
        };
    }, [isRoadmapNotReady]);

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
                const downloadUrl =
                    (typeof meta.download_url === "string" && meta.download_url)
                    || (typeof meta.file_url === "string" && meta.file_url)
                    || (typeof meta.template_url === "string" && meta.template_url)
                    || (typeof meta.source_url === "string" && meta.source_url)
                    || doc.source_url
                    || null;

                return {
                    id: doc.id,
                    title: doc.title,
                    description: doc.description,
                    completed: doc.metadata_json?.completed === true,
                    stepTitle: currentStep.title,
                    downloadUrl,
                };
            });
    }, [currentStep]);

    const handleAskLegal = async () => {
        const question = legalQuestion.trim();
        if (!question) {
            setLegalError("질문을 입력해 주세요.");
            return;
        }
        setLegalLoading(true);
        setLegalError(null);
        setLegalAnswer(null);
        try {
            const response = await apiClient.post<{ answer: string }>("/rag/query", { question });
            setLegalAnswer(response.data.answer);
        } catch (e) {
            console.error("Failed to query legal assistant", e);
            setLegalError("법률 AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요.");
        } finally {
            setLegalLoading(false);
        }
    };

    if (isLoading || !data) {
        return <div className="p-8 text-center">Loading...</div>;
    }

    if (isRoadmapNotReady) {
        return (
            <RoadmapGenerationPanel
                isAuthenticated={isLoggedIn}
                onRefresh={() => void reload()}
                onGenerated={() => void reload()}
            />
        );
    }

    return (
        <div className="">
            {/* Main Grid: 4 Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

                {/* 1. Progress Card (Span 3) */}
                <div className="md:col-span-3 lg:col-span-3 h-full">
                    <ProgressCard
                        phase={data.current_phase}
                        daysLeft={data.stats.days_left}
                        nextTitle={nextRoadmapTitle}
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
                                            {doc.downloadUrl ? (
                                                <a
                                                    href={doc.downloadUrl}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    download
                                                    className="inline-flex rounded-md border border-blue-200 bg-blue-50 px-2 py-1 text-[11px] font-semibold text-blue-700 hover:bg-blue-100"
                                                >
                                                    다운로드
                                                </a>
                                            ) : (
                                                <span className="text-[11px] text-slate-400">
                                                    다운로드 링크 없음
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

            {/* Floating FAB */}
            <div className="fixed bottom-28 md:bottom-8 right-6 md:right-8 z-50">
                <Button
                    onClick={() => {
                        setIsLegalModalOpen(true);
                    }}
                    className="w-14 h-14 md:w-auto md:h-auto group flex items-center justify-center md:justify-start md:gap-3 bg-slate-900 hover:bg-slate-800 text-white p-0 md:pl-4 md:pr-6 md:py-4 rounded-full shadow-[0_4px_20px_rgba(54,164,242,0.4)] transition-all hover:scale-105 active:scale-95 border-none"
                >
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="hidden md:block font-bold text-sm tracking-tight text-white">법률 AI에게 물어보기</span>
                </Button>
            </div>
            <Dialog open={isLegalModalOpen} onOpenChange={setIsLegalModalOpen}>
                <DialogContent className="sm:max-w-2xl">
                    <DialogHeader>
                        <DialogTitle>법률 AI 질의</DialogTitle>
                    </DialogHeader>
                    <div className="space-y-3">
                        <textarea
                            value={legalQuestion}
                            onChange={(e) => setLegalQuestion(e.target.value)}
                            rows={4}
                            placeholder="예: 강남구 휴게음식점 창업 시 영업신고/위생 관련 필수 절차는?"
                            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                        <div className="flex items-center gap-2">
                            <Button
                                onClick={() => void handleAskLegal()}
                                disabled={legalLoading}
                                className="bg-slate-900 text-white hover:bg-slate-800"
                            >
                                {legalLoading ? "질의 중..." : "질의하기"}
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => {
                                    setLegalQuestion("");
                                    setLegalAnswer(null);
                                    setLegalError(null);
                                }}
                            >
                                초기화
                            </Button>
                        </div>
                        {legalError ? (
                            <p className="text-sm text-red-600">{legalError}</p>
                        ) : null}
                        {legalAnswer ? (
                            <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 text-sm text-slate-700 whitespace-pre-wrap">
                                {legalAnswer}
                            </div>
                        ) : null}
                    </div>
                </DialogContent>
            </Dialog>
        </div>
    );
};
