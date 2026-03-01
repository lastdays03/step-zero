"use client";

import { useCallback, useState } from "react";
import { apiClient } from "@/lib/api-client";

export interface RoadmapIntakePayload {
    business_type: string;
    location: string;
    description: string;
    startup_type: string;
    startup_method: string;
    open_timeline: string;
    budget_range: string;
    additional_notes: string;
    goal_horizon_days: number;
    experience_level: string;
}

export interface RoadmapJobStatus {
    job_id: string;
    status: "QUEUED" | "RUNNING" | "SUCCEEDED" | "FAILED";
    stage: string;
    progress: number;
    roadmap_id?: string | null;
    error_code?: string | null;
    error_message?: string | null;
}

interface JobResultResponse {
    job_id: string;
    status: string;
    roadmap_id?: string | null;
}

export const useRoadmapJob = () => {
    const [job, setJob] = useState<RoadmapJobStatus | null>(null);
    const [error, setError] = useState<string | null>(null);

    const startJob = useCallback(async (payload: RoadmapIntakePayload): Promise<string> => {
        setError(null);
        const response = await apiClient.post<RoadmapJobStatus>("/roadmaps/jobs", payload);
        setJob(response.data);
        return response.data.job_id;
    }, []);

    const fetchJob = useCallback(async (jobId: string): Promise<RoadmapJobStatus> => {
        const response = await apiClient.get<RoadmapJobStatus>(`/roadmaps/jobs/${jobId}`);
        setJob(response.data);
        return response.data;
    }, []);

    const fetchResult = useCallback(async (jobId: string): Promise<JobResultResponse> => {
        const response = await apiClient.get<JobResultResponse>(`/roadmaps/jobs/${jobId}/result`);
        return response.data;
    }, []);

    return { job, error, setError, startJob, fetchJob, fetchResult };
};
