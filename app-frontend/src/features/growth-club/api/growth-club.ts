import { apiClient } from '@/lib/api-client';
import { Post } from '../types';

export const growthClubApi = {
    getPosts: async (category: string = 'all', search?: string, searchType?: string): Promise<Post[]> => {
        const params: { category: string; search?: string; search_type?: string } = { category };
        if (search) params.search = search;
        if (searchType) params.search_type = searchType;
        try {
            const res = await apiClient.get<Post[]>('/growth-club/posts', { params });
            return res.data;
        } catch (error) {
            console.error('getPosts error:', error);
            throw error;
        }
    },

    createPost: async (formData: FormData): Promise<Post> => {
        try {
            const res = await apiClient.post<Post>('/growth-club/posts', formData);
            return res.data;
        } catch (error) {
            console.error('createPost error:', error);
            throw error;
        }
    },

    addComment: async (postId: number, content: string, parentId?: number) => {
        try {
            const res = await apiClient.post('/growth-club/comments', {
                post_id: postId,
                content,
                parent_id: parentId
            });
            return res.data;
        } catch (error) {
            console.error('addComment error:', error);
            throw error;
        }
    },

    reportPost: async (postId: number, reason: string) => {
        try {
            const res = await apiClient.post(`/growth-club/posts/${postId}/report`, { reason });
            return res.data;
        } catch (error) {
            console.error('reportPost error:', error);
            throw error;
        }
    },

    deletePost: async (postId: number) => {
        try {
            const res = await apiClient.delete(`/growth-club/posts/${postId}`);
            return res.data;
        } catch (error) {
            console.error('deletePost error:', error);
            throw error;
        }
    },

    deleteComment: async (commentId: number) => {
        try {
            const res = await apiClient.delete(`/growth-club/comments/${commentId}`);
            return res.data;
        } catch (error) {
            console.error('deleteComment error:', error);
            throw error;
        }
    },

    likePost: async (postId: number): Promise<{ liked: boolean; likes_count: number }> => {
        try {
            const res = await apiClient.post(`/growth-club/posts/${postId}/like`);
            return res.data;
        } catch (error) {
            console.error('likePost error:', error);
            throw error;
        }
    },

    reportComment: async (commentId: number, reason: string) => {
        try {
            const res = await apiClient.post(`/growth-club/comments/${commentId}/report`, { reason });
            return res.data;
        } catch (error) {
            console.error('reportComment error:', error);
            throw error;
        }
    }
};

