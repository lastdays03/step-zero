"use client";

import { useEffect, useState } from "react";
import { ROADMAP_POLLING_CLEARED_EVENT, apiClient } from "@/lib/api-client";
import { RoadmapChatIntake, type RoadmapRawInput, type RoadmapValidationResult } from "./RoadmapChatIntake";
import { mapJobFailureMessage, VALIDATE_FALLBACK_MESSAGE } from "./roadmap-constants";
import { useRoadmapJob } from "@/features/roadmap/hooks";
import type { RoadmapIntakePayload } from "@/features/roadmap/hooks/useRoadmapJob";
import { SocialAuthModal } from "@/features/auth/components/SocialAuthModal";

interface RoadmapInputValidateResponse {
    valid: boolean;
    normalized_business_type?: string | null;
    normalized_location?: string | null;
    reason?: string | null;
    confidence: number;
}

const ROADMAP_JOB_STORAGE_KEY = "roadmap_polling_job_id";

interface RoadmapGenerationPanelProps {
    isAuthenticated: boolean;
    onRefresh?: () => void;
    onGenerated: (roadmapId: string | number) => Promise<void> | void;
    onCancel?: () => void;
}

export const RoadmapGenerationPanel = ({
    isAuthenticated,
    onRefresh,
    onGenerated,
}: RoadmapGenerationPanelProps) => {
    const { job, startJob, fetchJob, fetchResult } = useRoadmapJob();
    const [pollingJobId, setPollingJobId] = useState<string | null>(() => {
        if (typeof window === "undefined") return null;
        return window.localStorage.getItem(ROADMAP_JOB_STORAGE_KEY);
    });
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

    useEffect(() => {
        const handlePollingCleared = () => {
            setPollingJobId(null);
            setGenerationError("로그인 만료로 로드맵 생성 확인이 중단되었습니다. 다시 로그인 후 재시도해 주세요.");
        };

        window.addEventListener(ROADMAP_POLLING_CLEARED_EVENT, handlePollingCleared);
        return () => {
            window.removeEventListener(ROADMAP_POLLING_CLEARED_EVENT, handlePollingCleared);
        };
    }, []);

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
                        if (!cancelled) {
                            window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
                            setPollingJobId(null);
                            await onGenerated(result.roadmap_id);
                        }
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
    }, [pollingJobId, fetchJob, fetchResult, onGenerated]);

    const handleValidateInput = async (input: RoadmapRawInput): Promise<RoadmapValidationResult> => {
        setGenerationError(null);
        const validateResponse = await apiClient.post<RoadmapInputValidateResponse>(
            "/roadmaps/jobs/validate",
            {
                business_type: input.business_type.trim(),
                location: input.location.trim(),
                description: input.description.trim(),
            }
        );
        const validation = validateResponse.data;
        if (!validation.valid) {
            const reason = validation.reason || VALIDATE_FALLBACK_MESSAGE;
            setGenerationError(reason);
            throw new Error(reason);
        }
        const normalizedBusiness = (validation.normalized_business_type || input.business_type).trim();
        const normalizedLocation = (validation.normalized_location || input.location).trim();
        return {
            payload: {
                business_type: normalizedBusiness,
                location: normalizedLocation,
                description: input.description.trim(),
                startup_type: input.startup_type.trim(),
                startup_method: input.startup_method.trim(),
                open_timeline: input.open_timeline.trim(),
                budget_range: input.budget_range.trim(),
                additional_notes: input.description.trim(),
                goal_horizon_days: 30,
                experience_level: "BEGINNER",
            },
            summary:
                `업종 '${normalizedBusiness}', 지역 '${normalizedLocation}', `
                + `형태 '${input.startup_type}', 방식 '${input.startup_method}', 오픈 '${input.open_timeline}', 예산 '${input.budget_range}'`,
        };
    };

    const handleStartGeneration = async (payload: RoadmapIntakePayload) => {
        const started = await startJob(payload);
        setGenerationError(null);
        setPollingJobId(started);
        window.localStorage.setItem(ROADMAP_JOB_STORAGE_KEY, started);
    };

    const handleCancelGenerating = () => {
        setPollingJobId(null);
        window.localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
    };

    return (
        <>
            <RoadmapChatIntake
                onValidate={handleValidateInput}
                onSubmit={handleStartGeneration}
                onRefresh={onRefresh}
                externalError={generationError || job?.error_message}
                isAuthenticated={isAuthenticated}
                onRequireLogin={() => setIsAuthModalOpen(true)}
                isGenerating={Boolean(pollingJobId)}
                generatingStatus={{
                    status: job?.status,
                    stage: job?.stage,
                    progress: job?.progress,
                }}
                onCancelGenerating={handleCancelGenerating}
            />
            <SocialAuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setIsAuthModalOpen(false)}
            />
        </>
    );
};
