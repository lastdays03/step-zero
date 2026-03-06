import { useState, useEffect, useCallback } from 'react';
import { apiClient } from '@/lib/api-client';
import type { DashboardResponse } from '@/lib/api-types';
import { AxiosError } from 'axios';

export type DashboardData = DashboardResponse;

const FALLBACK_CURRENT_PHASE = {
    title: '로드맵을 생성해 보세요',
    progress: 0,
    status: 'GUEST' as const,
};

export const useDashboard = (roadmapId?: string | null) => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const params: Record<string, string> = {};
            if (roadmapId) params.roadmap_id = roadmapId;
            const response = await apiClient.get('/dashboard', { params });
            setData(response.data);
        } catch (err) {
            console.error('Failed to load dashboard data:', err);
            const status = err instanceof AxiosError ? err.response?.status : undefined;
            if (status === 401) {
                setError('로그인이 만료되었습니다. 다시 로그인해 주세요.');
            } else {
                setError('데이터를 불러오는 중 오류가 발생했습니다.');
            }
            setData((prev) => prev ?? {
                user_name: 'Guest',
                current_phase: FALLBACK_CURRENT_PHASE,
                roadmap: [],
                stats: { days_left: 0, tasks_completed: 0, total_tasks: 0 },
                growth_club: { founders_online: 0 },
            });
        } finally {
            setLoading(false);
        }
    }, [roadmapId]);

    useEffect(() => {
        void loadData();

        const handleAuthChange = () => {
            void loadData();
        };

        window.addEventListener('auth-storage-changed', handleAuthChange);
        window.addEventListener('storage', handleAuthChange);

        return () => {
            window.removeEventListener('auth-storage-changed', handleAuthChange);
            window.removeEventListener('storage', handleAuthChange);
        };
    }, [loadData]);

    return { data, loading, error, reload: loadData };
};
