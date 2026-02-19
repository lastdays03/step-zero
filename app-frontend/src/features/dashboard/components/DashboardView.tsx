"use client";

import React, { useEffect, useState } from 'react';
import { useDashboard } from '../hooks/useDashboard';
import { ProgressCard } from './ProgressCard';
import { RoadmapStepper } from './RoadmapStepper';
import { GrowthClubCard } from './GrowthClubCard';
import { RoadmapEmptyHero, RoadmapGeneratingState } from '@/features/roadmap/components';
import { useRoadmapJob } from '@/features/roadmap/hooks';
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Sparkles, Clock, CheckSquare } from 'lucide-react';

const ROADMAP_JOB_STORAGE_KEY = "roadmap_polling_job_id";

const mapJobFailureMessage = (errorCode?: string | null, errorMessage?: string | null): string => {
    if (errorMessage?.trim()) return errorMessage;
    switch (errorCode) {
        case "QUEUE_UNAVAILABLE":
            return "작업 대기열 연결이 불안정합니다. 잠시 후 다시 시도해 주세요.";
        case "VALIDATION_FAILED":
            return "입력값 검증에 실패했습니다. 업종/지역 정보를 다시 확인해 주세요.";
        case "GENERATION_TIMEOUT":
            return "로드맵 생성 시간이 초과되었습니다. 다시 시도해 주세요.";
        case "GENERATION_FAILED":
            return "AI 로드맵 생성 중 오류가 발생했습니다. 다시 시도해 주세요.";
        default:
            return "로드맵 생성에 실패했습니다. 잠시 후 다시 시도해 주세요.";
    }
};

export const DashboardView = () => {
    const { data, loading: isLoading } = useDashboard();
    const { job, fetchJob, fetchResult } = useRoadmapJob();
    const [pollingJobId, setPollingJobId] = useState<string | null>(() => {
        if (typeof window === "undefined") return null;
        return window.localStorage.getItem(ROADMAP_JOB_STORAGE_KEY);
    });
    const [generationError, setGenerationError] = useState<string | null>(null);

    useEffect(() => {
        if (!pollingJobId) return;
        let cancelled = false;
        let timer: ReturnType<typeof setTimeout> | null = null;
        const startedAt = Date.now();

        const poll = async () => {
            if (cancelled) return;
            try {
                const status = await fetchJob(pollingJobId);
                if (status.status === "SUCCEEDED") {
                    const result = await fetchResult(pollingJobId);
                    if (result.roadmap_id) {
                        window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                        window.location.reload();
                        return;
                    }
                }
                if (status.status === "FAILED") {
                    if (!cancelled) {
                        setGenerationError(mapJobFailureMessage(status.error_code, status.error_message));
                        setPollingJobId(null);
                        window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                    }
                    return;
                }
                const elapsed = Date.now() - startedAt;
                const nextInterval = elapsed > 30_000 ? 3000 : 2000;
                timer = setTimeout(() => void poll(), nextInterval);
            } catch (e) {
                console.error(e);
                if (!cancelled) {
                    setGenerationError("생성 상태를 확인하는 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
                    setPollingJobId(null);
                    window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                }
            }
        };
        void poll();

        return () => {
            cancelled = true;
            if (timer) clearTimeout(timer);
        };
    }, [pollingJobId, fetchJob, fetchResult]);

    if (isLoading || !data) {
        return <div className="p-8 text-center">Loading...</div>;
    }

    if (data.roadmap.length === 0) {
        if (pollingJobId) {
            return (
                <RoadmapGeneratingState
                    onCancel={() => {
                        setPollingJobId(null);
                        window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                    }}
                    status={job?.status}
                    stage={job?.stage}
                    progress={job?.progress}
                    errorMessage={generationError || job?.error_message}
                />
            );
        }
        return (
            <RoadmapEmptyHero
                title="StepZero와 함께 당신의 비즈니스 여정을 시작하세요"
                subtitle="아직 생성된 로드맵이 없습니다. 첫 로드맵을 생성하면 대시보드 진행 현황이 자동으로 채워집니다."
                onPrimaryClick={() => {
                    window.location.href = "/roadmap?start=1";
                }}
                primaryLabel="로드맵 생성하러 가기"
            />
        );
    }

    return (
        <div className="">
            {/* Main Grid: 4 Columns */}
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">

                {/* 1. Progress Card (Span 3) */}
                <div className="md:col-span-3 lg:col-span-3 h-full">
                    <ProgressCard phase={data.current_phase} />
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
                            <p className="text-sm text-slate-400 text-center py-4">로드맵을 생성하면 필요한 서류 목록이 표시됩니다.</p>
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
                <Button className="w-14 h-14 md:w-auto md:h-auto group flex items-center justify-center md:justify-start md:gap-3 bg-slate-900 hover:bg-slate-800 text-white p-0 md:pl-4 md:pr-6 md:py-4 rounded-full shadow-[0_4px_20px_rgba(54,164,242,0.4)] transition-all hover:scale-105 active:scale-95 border-none">
                    <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shrink-0">
                        <Sparkles className="w-4 h-4 text-white" />
                    </div>
                    <span className="hidden md:block font-bold text-sm tracking-tight text-white">법률 AI에게 물어보기</span>
                </Button>
            </div>
        </div>
    );
};
