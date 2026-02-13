import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

// Define return type interface (matching backend response)
export interface DashboardData {
    user_name: string;
    current_phase: {
        title: string;
        progress: number;
        status: string;
    };
    roadmap: Array<{
        title: string;
        status: string;
        date: string;
    }>;
    stats: {
        days_left: number;
        tasks_completed: number;
        total_tasks: number;
    };
    growth_club: {
        founders_online: number;
    };
}

const GUEST_DASHBOARD_DATA: DashboardData = {
    user_name: 'Guest',
    current_phase: {
        title: '로드맵을 생성해 보세요',
        progress: 0,
        status: 'GUEST',
    },
    roadmap: [
        { title: 'Step 1: 아이디어 검증', status: 'locked', date: '-' },
        { title: 'Step 2: 법인 설립', status: 'locked', date: '-' },
        { title: 'Step 3: 비즈니스 계좌', status: 'locked', date: '-' },
    ],
    stats: {
        days_left: 0,
        tasks_completed: 0,
        total_tasks: 0,
    },
    growth_club: {
        founders_online: 1250,
    },
};

export const useDashboard = () => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                // actual API call
                const response = await apiClient.get('/dashboard');
                setData(response.data);
            } catch (err) {
                console.error('Failed to load dashboard data:', err);
                setError('데이터를 불러오는 중 오류가 발생했습니다.');
                setData(GUEST_DASHBOARD_DATA);
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return { data, loading, error };
};
