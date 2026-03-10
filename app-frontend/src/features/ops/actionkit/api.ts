import { apiClient } from "@/lib/api-client";

export interface ActionKitOpsSummary {
    total_items: number;
    items_with_files: number;
    inactive_items: number;
    total_related_laws: number;
    total_highlights: number;
}

export const fetchSummary = async () => {
    const { data } = await apiClient.get('/ops/actionkit/summary');
    return data;
};

export const fetchCategories = async () => {
    const { data } = await apiClient.get('/ops/actionkit/categories');
    return data;
};

export const createCategory = async (payload: { domain: string, slug: string, title: string, sort_order: number, is_active: boolean }) => {
    const { data } = await apiClient.post('/ops/actionkit/categories', payload);
    return data;
};

export const updateCategory = async (categoryId: number, payload: { slug?: string, title?: string, sort_order?: number, is_active?: boolean }) => {
    const { data } = await apiClient.patch(`/ops/actionkit/categories/${categoryId}`, payload);
    return data;
};

export const deleteCategory = async (categoryId: number) => {
    const { data } = await apiClient.delete(`/ops/actionkit/categories/${categoryId}`);
    return data;
};

export const fetchCategoryItems = async (categoryId: number) => {
    const { data } = await apiClient.get(`/ops/actionkit/categories/${categoryId}/items`);
    return data;
};

export const fetchItemDetail = async (itemId: number) => {
    const { data } = await apiClient.get(`/ops/actionkit/items/${itemId}`);
    return data;
};

export const updateItemOrders = async (items: { id: number, sort_order: number }[]) => {
    const { data } = await apiClient.patch('/ops/actionkit/items/reorder', { items });
    return data;
};

// ── ActionKit Stats ──

export interface ActionKitKPI {
    downloads: number;
    downloads_delta: number | null;
    active_users: number;
    active_users_delta: number | null;
    per_user: number;
    per_user_delta: number | null;
}

export interface PopularItem {
    item_id: number;
    count: number;
    trend: number | null;
}

export interface SearchKeyword {
    keyword: string;
    count: number;
}

export interface ActionKitStatsResponse {
    kpi: ActionKitKPI;
    popular_items: PopularItem[];
    search_keywords: SearchKeyword[];
    insight: string | null;
    range_days: number;
    generated_at: string;
}

export const fetchStats = async (rangeDays: number = 30): Promise<ActionKitStatsResponse> => {
    const { data } = await apiClient.get(`/ops/actionkit/stats?range_days=${rangeDays}`);
    return data;
};

// ── User Tracking ──

export const trackEvent = (payload: {
    event_type: string;
    item_id?: number;
    search_query?: string;
}) => {
    apiClient.post('/actionkits/track', payload).catch(() => {});
};
