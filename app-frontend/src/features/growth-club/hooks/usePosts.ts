import { useState, useEffect, useCallback } from 'react';
import { Post } from '../types';
import { growthClubApi } from '../api';

export const usePosts = (category: string = 'all', search?: string) => {
    const [posts, setPosts] = useState<Post[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<Error | null>(null);

    const fetchPosts = useCallback(async () => {
        setIsLoading(true);
        try {
            const data = await growthClubApi.getPosts(category, search);
            setPosts(data);
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to fetch posts'));
        } finally {
            setIsLoading(false);
        }
    }, [category, search]);

    useEffect(() => {
        fetchPosts();
    }, [fetchPosts]);

    return {
        posts,
        isLoading,
        error,
        refetch: fetchPosts,
    };
};
