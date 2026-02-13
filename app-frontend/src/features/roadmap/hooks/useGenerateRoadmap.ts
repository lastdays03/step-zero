"use client";

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export interface GenerationRequest {
    business_type: string;
    location: string;
    description: string;
}

export interface RoadmapStep {
    id: number;
    title: string;
    status: string;
}

export interface GenerationResponse {
    roadmap_id: string;
    title: string;
    steps: RoadmapStep[];
}

export const useGenerateRoadmap = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generate = async (params: GenerationRequest): Promise<GenerationResponse | null> => {
        setLoading(true);
        setError(null);
        try {
            const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
            const response = await apiClient.post<GenerationResponse>('/generate', params, {
                headers: token ? { Authorization: `Bearer ${token}` } : undefined
            });
            return response.data;
        } catch (err) {
            setError('로드맵 생성에 실패했습니다.');
            console.error(err);
            return null;
        } finally {
            setLoading(false);
        }
    };

    return { generate, loading, error };
};
