export interface UserProfile {
    id: number;
    user_id: number;
    full_name?: string | null;
    nickname?: string | null;
    profile_img?: string | null;
    is_public: boolean;
    category?: string | null;
    region?: string | null;
    philosophy?: string | null;
    experiences: string[];
    awards: string[];
    certificates: string[];
    updated_at: string;
    completeness_rate: number;
    email?: string | null;
}

export type UserProfileUpdate = Partial<Omit<UserProfile, 'id' | 'user_id' | 'updated_at' | 'completeness_rate'>>;
