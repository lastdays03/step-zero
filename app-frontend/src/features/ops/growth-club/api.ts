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
