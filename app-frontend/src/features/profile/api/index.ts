import { apiClient } from '@/lib/api-client';
import { UserProfile, UserProfileUpdate } from '../types';

export const getMyProfile = async (): Promise<UserProfile> => {
    // 캐시 방지를 위해 타임스탬프 추가
    const response = await apiClient.get<UserProfile>(`/profile/me?t=${Date.now()}`);
    return response.data;
};

export const updateMyProfile = async (data: UserProfileUpdate): Promise<UserProfile> => {
    const response = await apiClient.put<UserProfile>('/profile/me', data);
    return response.data;
};

export const uploadProfileImage = async (file: File): Promise<UserProfile> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiClient.post<UserProfile>('/profile/me/image', formData);
    return response.data;
};
