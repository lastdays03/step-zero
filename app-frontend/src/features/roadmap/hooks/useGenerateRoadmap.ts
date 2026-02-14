"use client";

import { useState } from 'react';
import { apiClient } from '@/lib/api-client';
import type { RoadmapCreateRequest, RoadmapResponse } from '@/lib/api-types';

export type GenerationRequest = RoadmapCreateRequest;
export type GenerationResponse = RoadmapResponse;

export const useGenerateRoadmap = () => {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const generate = async (params: GenerationRequest): Promise<GenerationResponse | null> => {
        setLoading(true);
        setError(null);
        try {
            const response = await apiClient.post<GenerationResponse>('/roadmaps', params);
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
