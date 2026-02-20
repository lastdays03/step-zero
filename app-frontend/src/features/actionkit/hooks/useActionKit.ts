import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { ActionKitData } from '../types';

export const useActionKit = () => {
    const [data, setData] = useState<ActionKitData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const response = await apiClient.get('/actionkits/kits');
                setData(response.data);
            } catch (err) {
                console.error('Failed to load action kit data:', err);
                setError('액션 키트 데이터를 불러오는 중 오류가 발생했습니다.');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return { data, loading, error };
};
