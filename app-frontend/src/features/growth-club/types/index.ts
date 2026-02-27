export type PostCategory = 'free' | 'notice' | 'neighborhood' | 'industry';

export interface Author {
    id: number;
    username: string;
    nickname?: string;
    email?: string;
    profile_img?: string;
    profile_image?: string;
    neighborhood?: string;
    industry?: string;
    is_public?: boolean;
    is_suspended?: boolean;
    suspended_at?: string;
}

export interface Comment {
    id: number;
    content: string;
    author: Author;
    created_at: string;
    replies?: Comment[];
    parent_id?: number;
    report_count?: number;
    is_blinded?: boolean;
    report_reason?: string;
}

export interface PostAttachment {
    id: number;
    kind: "image" | "file";
    object_key: string;
    original_filename?: string;
    mime_type?: string;
    size_bytes?: number;
    created_at: string;
}

export interface Post {
    id: number;
    title: string;
    content: string;
    category: PostCategory;
    neighborhood: string;
    industry: string;
    author: Author;
    created_at: string;
    comments: Comment[];
    attachments?: PostAttachment[];
    report_count: number;
    is_blinded?: boolean;
    report_reason?: string;
    likes_count: number;
    is_liked: boolean;
}
