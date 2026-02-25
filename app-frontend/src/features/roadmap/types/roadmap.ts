
export interface RoadmapNodeData {
    id: string;
    title: string;
    children: RoadmapNodeData[];
}

export interface RoadmapSummary {
    roadmap_id: string;
    title: string;
    business_type: string;
    location: string;
    created_at: string;
    progress: number;
    total_steps: number;
    completed_steps: number;
}

export interface RoadmapListResponse {
    items: RoadmapSummary[];
    total: number;
}

export type { RoadmapDetailResponse } from "../components/roadmap-utils";
