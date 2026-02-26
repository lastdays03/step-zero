import { apiClient } from "@/lib/api-client";
import { Post, Comment } from "@/features/growth-club/types";

export const fetchBlindedPosts = async (): Promise<Post[]> => {
    const response = await apiClient.get<Post[]>("/ops/growth-club/posts/blinded");
    return response.data;
};

export const unblindPost = async (postId: number): Promise<void> => {
    await apiClient.post(`/ops/growth-club/posts/${postId}/unblind`);
};

export const fetchBlindedComments = async (): Promise<Comment[]> => {
    const response = await apiClient.get<Comment[]>("/ops/growth-club/comments/blinded");
    return response.data;
};

export const unblindComment = async (commentId: number): Promise<void> => {
    await apiClient.post(`/ops/growth-club/comments/${commentId}/unblind`);
};

export const suspendUser = async (userId: number, reason: string, targetType: "POST" | "COMMENT", targetId: number): Promise<string> => {
    const res = await apiClient.post<{ suspended_at: string }>(`/ops/growth-club/users/${userId}/suspend`, {
        reason,
        target_type: targetType,
        target_id: targetId
    });
    return res.data.suspended_at;
};

export const unsuspendUser = async (userId: number): Promise<void> => {
    await apiClient.post(`/ops/growth-club/users/${userId}/unsuspend`);
};

export const deletePost = async (postId: number): Promise<void> => {
    await apiClient.delete(`/ops/growth-club/posts/${postId}`);
};

export const deleteComment = async (commentId: number): Promise<void> => {
    await apiClient.delete(`/ops/growth-club/comments/${commentId}`);
};
