export type PostCategory = 'free' | 'notice' | 'neighborhood' | 'industry';

export interface Author {
    id: number;
    username: string;
    neighborhood?: string;
    industry?: string;
    profile_image?: string;
}

export interface Comment {
    id: number;
    content: string;
    author: Author;
    created_at: string;
    replies?: Comment[];
    parent_id?: number;
}

export interface Post {
    id: number;
    title: string;
    content: string;
    category: PostCategory;
    neighborhood: string;
    industry: string;
    image_path?: string;
    file_path?: string;
    author: Author;
    created_at: string;
    comments: Comment[];
    report_count: number;
    likes_count: number;
    is_liked: boolean;
}

