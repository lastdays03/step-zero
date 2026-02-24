import { apiClient } from "@/lib/api-client";
import { ActionKitItem, ActionKitCategory } from "@/features/actionkit/types";

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

export const fetchCategoryItems = async (categoryId: number) => {
    const { data } = await apiClient.get(`/ops/actionkit/categories/${categoryId}/items`);
    return data;
};
