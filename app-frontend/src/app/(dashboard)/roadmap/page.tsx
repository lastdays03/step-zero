"use client";

import { useCallback, useEffect, useState } from "react";
import { apiClient } from "@/lib/api-client";
import {
    RoadmapExecutionView,
    type RoadmapDetailResponse,
} from "@/features/roadmap/components/RoadmapExecutionView";
import { RoadmapGenerationPanel } from "@/features/roadmap/components";
import type { DashboardResponse } from "@/lib/api-types";
import { useAuth } from "@/providers/AuthProvider";

export default function RoadmapPage() {
    const { isLoggedIn } = useAuth();
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [hasRoadmap, setHasRoadmap] = useState(false);
    const [generated, setGenerated] = useState<RoadmapDetailResponse | null>(null);
    const [updatingStepId, setUpdatingStepId] = useState<number | null>(null);
    const [updatingActionId, setUpdatingActionId] = useState<number | null>(null);

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

    if (!hasRoadmap) {
        return (
            <RoadmapGenerationPanel
                isAuthenticated={isLoggedIn}
                onRefresh={() => void loadStatus()}
                onGenerated={async (roadmapId) => {
                    const detail = await apiClient.get<RoadmapDetailResponse>(
                        `/roadmaps/${roadmapId}/detail`
                    );
                    setGenerated(detail.data);
                    setHasRoadmap(true);
                }}
            />
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
