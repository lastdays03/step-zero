import { apiClient } from "@/lib/api-client";

export interface ActionKitOpsSummary {
    total_items: number;
    pending_reviews: number;
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
