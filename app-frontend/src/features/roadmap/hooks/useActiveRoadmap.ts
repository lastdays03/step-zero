"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchRoadmapDetail } from "../api";
import type { RoadmapDetailResponse } from "../components/roadmap-utils";

const STORAGE_KEY = "stepzero_active_roadmap_id";

export interface UseActiveRoadmapReturn {
    activeRoadmapId: string | null;
    activeRoadmap: RoadmapDetailResponse | null;
    loading: boolean;
    error: string | null;
    setActiveRoadmap: (roadmapId: string) => Promise<void>;
    clearActiveRoadmap: () => void;
    reloadActiveRoadmap: () => Promise<void>;
}

export function useActiveRoadmap(): UseActiveRoadmapReturn {
    const [activeRoadmapId, setActiveRoadmapId] = useState<string | null>(null);
    const [activeRoadmap, setActiveRoadmap] =
        useState<RoadmapDetailResponse | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadDetail = useCallback(async (roadmapId: string) => {
        setLoading(true);
        setError(null);
        try {
            const detail = await fetchRoadmapDetail(roadmapId);
            setActiveRoadmapId(roadmapId);
            setActiveRoadmap(detail);
        } catch (err: unknown) {
            const status =
                err && typeof err === "object" && "response" in err
                    ? (err as { response?: { status?: number } }).response
                          ?.status
                    : undefined;
            if (status === 404) {
                localStorage.removeItem(STORAGE_KEY);
                setActiveRoadmapId(null);
                setActiveRoadmap(null);
                setError(null);
            } else {
                setError("로드맵을 불러오는데 실패했습니다.");
            }
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        const storedId = localStorage.getItem(STORAGE_KEY);
        if (storedId) {
            loadDetail(storedId);
        }
    }, [loadDetail]);

    const setActiveRoadmapFn = useCallback(
        async (roadmapId: string) => {
            localStorage.setItem(STORAGE_KEY, roadmapId);
            await loadDetail(roadmapId);
        },
        [loadDetail],
    );

    const clearActiveRoadmap = useCallback(() => {
        localStorage.removeItem(STORAGE_KEY);
        setActiveRoadmapId(null);
        setActiveRoadmap(null);
        setError(null);
    }, []);

    const reloadActiveRoadmap = useCallback(async () => {
        const currentId = localStorage.getItem(STORAGE_KEY);
        if (currentId) {
            await loadDetail(currentId);
        }
    }, [loadDetail]);

    return {
        activeRoadmapId,
        activeRoadmap,
        loading,
        error,
        setActiveRoadmap: setActiveRoadmapFn,
        clearActiveRoadmap,
        reloadActiveRoadmap,
    };
}
