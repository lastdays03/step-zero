import { apiClient } from "@/lib/api-client";
import type { RoadmapListResponse, RoadmapSummary } from "../types/roadmap";
import type { RoadmapDetailResponse } from "../components/roadmap-utils";

export async function fetchRoadmapList(
    offset = 0,
    limit = 20,
): Promise<RoadmapListResponse> {
    const { data } = await apiClient.get<RoadmapListResponse>("/roadmaps", {
        params: { offset, limit },
    });
    return data;
}

export async function deleteRoadmap(roadmapId: string): Promise<void> {
    await apiClient.delete(`/roadmaps/${roadmapId}`);
}

export async function updateRoadmapTitle(
    roadmapId: string,
    title: string,
): Promise<RoadmapSummary> {
    const { data } = await apiClient.patch<RoadmapSummary>(
        `/roadmaps/${roadmapId}`,
        { title },
    );
    return data;
}

export async function fetchRoadmapDetail(
    roadmapId: string,
): Promise<RoadmapDetailResponse> {
    const { data } = await apiClient.get<RoadmapDetailResponse>(
        `/roadmaps/${roadmapId}/detail`,
    );
    return data;
}
