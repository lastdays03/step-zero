
import { useState, useEffect } from 'react';
import { fetchDashboardMock } from '../mocks/dashboardMock';

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

export const useDashboard = () => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const dashboardData = await fetchDashboardMock();
                setData(dashboardData);
            } catch (err) {
                console.error('Failed to load dashboard data:', err);
                setError('데이터를 불러오는 중 오류가 발생했습니다.');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return { data, loading, error };
};
