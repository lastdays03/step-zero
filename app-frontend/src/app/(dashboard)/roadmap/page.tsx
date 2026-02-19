"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import { RoadmapEmptyHero } from "@/features/roadmap/components/RoadmapEmptyHero";
import {
    RoadmapExecutionView,
    type RoadmapDetailResponse,
} from "@/features/roadmap/components/RoadmapExecutionView";
import { RoadmapGeneratingState } from "@/features/roadmap/components/RoadmapGeneratingState";
import { useRoadmapJob } from "@/features/roadmap/hooks";
import type { RoadmapIntakePayload } from "@/features/roadmap/hooks/useRoadmapJob";
import type { DashboardResponse } from "@/lib/api-types";

interface RoadmapInputValidateResponse {
    valid: boolean;
    normalized_business_type?: string | null;
    normalized_location?: string | null;
    reason?: string | null;
    confidence: number;
}

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

export default function RoadmapPage() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [hasRoadmap, setHasRoadmap] = useState(false);
    const [showForm, setShowForm] = useState(false);
    const [autoStartRequested, setAutoStartRequested] = useState(false);
    const [pollingJobId, setPollingJobId] = useState<string | null>(null);
    const [generated, setGenerated] = useState<RoadmapDetailResponse | null>(null);
    const [updatingStepId, setUpdatingStepId] = useState<number | null>(null);
    const [updatingActionId, setUpdatingActionId] = useState<number | null>(null);
    const [businessType, setBusinessType] = useState("");
    const [location, setLocation] = useState("");
    const [description, setDescription] = useState("");
    const [validating, setValidating] = useState(false);
    const [validationSummary, setValidationSummary] = useState<string | null>(null);
    const { job, startJob, fetchJob, fetchResult } = useRoadmapJob();

    const loadLatestRoadmapDetail = useCallback(async () => {
        const response = await apiClient.get<RoadmapDetailResponse>("/roadmaps/latest/detail");
        setGenerated(response.data);
    }, []);

    const loadStatus = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.get<DashboardResponse>("/dashboard");
            const phaseStatus = response.data.current_phase.status;
            const hasExistingRoadmap =
                response.data.roadmap.length > 0 &&
                phaseStatus !== "GUEST" &&
                phaseStatus !== "READY";
            setHasRoadmap(hasExistingRoadmap);
            if (hasExistingRoadmap) {
                setShowForm(false);
                setAutoStartRequested(false);
                setPollingJobId(null);
                if (typeof window !== "undefined") {
                    window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                }
                await loadLatestRoadmapDetail();
            } else {
                setGenerated(null);
            }
        } catch (e) {
            console.error("Failed to load roadmap status", e);
            setError("로드맵 상태를 불러오지 못했습니다. 다시 시도해 주세요.");
        } finally {
            setLoading(false);
        }
    }, [loadLatestRoadmapDetail]);

    useEffect(() => {
        void loadStatus();
    }, [loadStatus]);

    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        if (params.get("start") === "1") {
            setAutoStartRequested(true);
        }
    }, []);

    useEffect(() => {
        if (!loading && autoStartRequested && !hasRoadmap) {
            setShowForm(true);
        }
    }, [loading, autoStartRequested, hasRoadmap]);

    useEffect(() => {
        if (loading || hasRoadmap) return;
        const savedJobId = window.localStorage.getItem(ROADMAP_JOB_STORAGE_KEY);
        if (savedJobId) {
            setShowForm(true);
            setPollingJobId(savedJobId);
        }
    }, [loading, hasRoadmap]);

    useEffect(() => {
        if (pollingJobId) {
            window.localStorage.setItem(ROADMAP_JOB_STORAGE_KEY, pollingJobId);
            return;
        }
        window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
    }, [pollingJobId]);

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
                        const detail = await apiClient.get<RoadmapDetailResponse>(
                            `/roadmaps/${result.roadmap_id}/detail`
                        );
                        if (!cancelled) {
                            setGenerated(detail.data);
                            setHasRoadmap(true);
                            setShowForm(false);
                            setPollingJobId(null);
                        }
                        return;
                    }
                }
                if (status.status === "FAILED") {
                    if (!cancelled) {
                        setGenerationError(mapJobFailureMessage(status.error_code, status.error_message));
                        setPollingJobId(null);
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
                }
            }
        };
        void poll();

        return () => {
            cancelled = true;
            if (timer) clearTimeout(timer);
        };
    }, [pollingJobId, fetchJob, fetchResult]);

    const handleStartGeneration = async (payload: RoadmapIntakePayload) => {
        const jobId = await startJob(payload);
        setError(null);
        setGenerationError(null);
        setShowForm(true);
        setPollingJobId(jobId);
    };

    const handlePollingClose = () => {
        setPollingJobId(null);
    };

    const handleStepStatusChange = async (
        stepId: number,
        status: "IN_PROGRESS" | "COMPLETED"
    ) => {
        setUpdatingStepId(stepId);
        setGenerationError(null);
        try {
            await apiClient.patch(`/roadmaps/tasks/${stepId}`, { status });
            await loadLatestRoadmapDetail();
        } catch (e) {
            console.error(e);
            setGenerationError("단계 상태를 변경하지 못했습니다. 잠시 후 다시 시도해 주세요.");
        } finally {
            setUpdatingStepId(null);
        }
    };

    const handleActionCompletionChange = async (
        stepId: number,
        actionId: number,
        completed: boolean
    ) => {
        setUpdatingActionId(actionId);
        setGenerationError(null);
        try {
            await apiClient.patch(`/roadmaps/tasks/${stepId}/actions/${actionId}`, { completed });
            await loadLatestRoadmapDetail();
        } catch (e) {
            console.error(e);
            setGenerationError("체크리스트 상태를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.");
        } finally {
            setUpdatingActionId(null);
        }
    };

    const handleValidateAndStart = async () => {
        const rawBusiness = businessType.trim();
        const rawLocation = location.trim();
        if (!rawBusiness || !rawLocation) {
            setGenerationError("업종과 지역은 필수입니다.");
            return;
        }
        setValidating(true);
        setGenerationError(null);
        setValidationSummary(null);
        try {
            const validateResponse = await apiClient.post<RoadmapInputValidateResponse>(
                "/roadmaps/jobs/validate",
                {
                    business_type: rawBusiness,
                    location: rawLocation,
                    description: description.trim(),
                }
            );
            const validation = validateResponse.data;
            if (!validation.valid) {
                setGenerationError(validation.reason || "입력값 검증에 실패했습니다.");
                return;
            }
            const normalizedBusiness = (validation.normalized_business_type || rawBusiness).trim();
            const normalizedLocation = (validation.normalized_location || rawLocation).trim();
            setValidationSummary(
                `검증 완료: 업종 '${normalizedBusiness}', 지역 '${normalizedLocation}'`
            );
            await handleStartGeneration({
                business_type: normalizedBusiness,
                location: normalizedLocation,
                description: description.trim(),
                goal_horizon_days: 30,
                experience_level: "BEGINNER",
            });
        } catch (e) {
            console.error(e);
            setGenerationError("입력 검증 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.");
        } finally {
            setValidating(false);
        }
    };

    if (loading) {
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-8">
                <h1 className="text-2xl font-bold text-slate-900">로드맵</h1>
                <p className="mt-2 text-sm text-slate-600">로드맵 상태를 확인하는 중입니다...</p>
            </section>
        );
    }

    if (error) {
        return (
            <section className="rounded-2xl border border-red-200 bg-white p-8">
                <h1 className="text-2xl font-bold text-slate-900">로드맵</h1>
                <p className="mt-2 text-sm text-red-600">{error}</p>
                <button
                    type="button"
                    onClick={() => void loadStatus()}
                    className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
                >
                    다시 시도
                </button>
            </section>
        );
    }

    if (!hasRoadmap && !showForm) {
        return (
            <RoadmapEmptyHero
                onPrimaryClick={() => setShowForm(true)}
                onRefreshClick={() => void loadStatus()}
            />
        );
    }

    if (showForm && !hasRoadmap) {
        if (pollingJobId) {
            return (
                <RoadmapGeneratingState
                    onCancel={handlePollingClose}
                    status={job?.status}
                    stage={job?.stage}
                    progress={job?.progress}
                    errorMessage={generationError || job?.error_message}
                />
            );
        }
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
                <h2 className="text-xl font-bold text-slate-900">로드맵 생성 정보 입력</h2>
                <p className="mt-1 text-sm text-slate-600">
                    업종/지역을 입력하면 AI가 유효성을 먼저 검증하고, 통과 시 바로 생성을 시작합니다.
                </p>
                <div className="mt-6 grid gap-4">
                    <label className="grid gap-2">
                        <span className="text-sm font-semibold text-slate-700">업종 (필수)</span>
                        <input
                            value={businessType}
                            onChange={(e) => setBusinessType(e.target.value)}
                            placeholder="예: 카페, 온라인 의류 쇼핑몰"
                            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                    </label>
                    <label className="grid gap-2">
                        <span className="text-sm font-semibold text-slate-700">지역 (필수)</span>
                        <input
                            value={location}
                            onChange={(e) => setLocation(e.target.value)}
                            placeholder="예: 서울특별시 강남구"
                            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                    </label>
                    <label className="grid gap-2">
                        <span className="text-sm font-semibold text-slate-700">추가 설명 (선택)</span>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="예: 1인 창업, 초기 자본 5천만 원"
                            rows={4}
                            className="w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-blue-400"
                        />
                    </label>
                </div>
                {validationSummary ? (
                    <p className="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">
                        {validationSummary}
                    </p>
                ) : null}
                {generationError ? (
                    <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                        {generationError}
                    </p>
                ) : null}
                <div className="mt-6 flex gap-3">
                    <button
                        type="button"
                        onClick={() => setShowForm(false)}
                        disabled={validating}
                        className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
                    >
                        취소
                    </button>
                    <button
                        type="button"
                        onClick={() => void handleValidateAndStart()}
                        disabled={validating}
                        className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500 disabled:opacity-60"
                    >
                        {validating ? "AI 검증 중..." : "검증 후 로드맵 생성"}
                    </button>
                </div>
            </section>
        );
    }

    if (generated) {
        return (
            <div className="space-y-4">
                {generationError ? (
                    <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{generationError}</p>
                ) : null}
                <RoadmapExecutionView
                    data={generated}
                    onStepStatusChange={handleStepStatusChange}
                    onActionCompletionChange={handleActionCompletionChange}
                    updatingStepId={updatingStepId}
                    updatingActionId={updatingActionId}
                />
            </div>
        );
    }

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-8">
            <h1 className="text-2xl font-bold text-slate-900">로드맵</h1>
            <p className="mt-2 text-sm text-slate-600">
                로드맵 데이터를 불러오는 중입니다.
            </p>
            <button
                type="button"
                onClick={() => void loadStatus()}
                className="mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
            >
                다시 시도
            </button>
        </section>
    );
}
