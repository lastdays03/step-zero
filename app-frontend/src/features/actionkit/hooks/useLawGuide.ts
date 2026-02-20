import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';
import { LawData, LawChapter } from '../types';

export const useLawGuide = () => {
    const [data, setData] = useState<LawData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const loadData = async () => {
            setLoading(true);
            try {
                const response = await apiClient.get('/actionkits/laws');
                setData(response.data);
            } catch (err) {
                console.error('Failed to load law guide data:', err);
                setError('법령 가이드 데이터를 불러오는 중 오류가 발생했습니다.');
            } finally {
                setLoading(false);
            }
        };

        loadData();
    }, []);

    return { data, loading, error };
};
