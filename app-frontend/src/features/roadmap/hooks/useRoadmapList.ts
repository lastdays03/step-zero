"use client";

import { useCallback, useState } from "react";
import {
    deleteRoadmap,
    fetchRoadmapList,
    updateRoadmapTitle,
} from "../api";
import type { RoadmapSummary } from "../types/roadmap";

export interface UseRoadmapListReturn {
    list: RoadmapSummary[];
    total: number;
    loading: boolean;
    error: string | null;
    loadList: () => Promise<void>;
    handleDelete: (roadmapId: string) => Promise<boolean>;
    handleRename: (roadmapId: string, newTitle: string) => Promise<boolean>;
}

export function useRoadmapList(): UseRoadmapListReturn {
    const [list, setList] = useState<RoadmapSummary[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const loadList = useCallback(async () => {
        setLoading(true);
        setError(null);
        try {
            const res = await fetchRoadmapList();
            setList(res.items);
            setTotal(res.total);
        } catch {
            setError("로드맵 목록을 불러오는데 실패했습니다.");
        } finally {
            setLoading(false);
        }
    }, []);

    const handleDelete = useCallback(
        async (roadmapId: string): Promise<boolean> => {
            try {
                await deleteRoadmap(roadmapId);
                await loadList();
                return true;
            } catch {
                setError("로드맵 삭제에 실패했습니다.");
                return false;
            }
        },
        [loadList],
    );

    const handleRename = useCallback(
        async (roadmapId: string, newTitle: string): Promise<boolean> => {
            try {
                await updateRoadmapTitle(roadmapId, newTitle);
                await loadList();
                return true;
            } catch {
                setError("로드맵 이름 변경에 실패했습니다.");
                return false;
            }
        },
        [loadList],
    );

    return {
        list,
        total,
        loading,
        error,
        loadList,
        handleDelete,
        handleRename,
    };
}
