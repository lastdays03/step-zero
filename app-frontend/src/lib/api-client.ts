import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";
import { getApiBaseUrl } from "./env";

export const AUTH_STORAGE_EVENT = "auth-storage-changed";
export const ROADMAP_POLLING_CLEARED_EVENT = "roadmap-polling-cleared";
const ROADMAP_JOB_STORAGE_KEY = "roadmap_polling_job_id";
const PROACTIVE_REFRESH_MARGIN_MS = 5 * 60 * 1000; // 5 minutes before expiry

const baseURL = getApiBaseUrl();

export const apiClient = axios.create({
    baseURL,
});

// --- Silent Refresh Infrastructure ---

let isRefreshing = false;
let failedQueue: {
    resolve: (token: string) => void;
    reject: (error: unknown) => void;
}[] = [];

const processQueue = (error: unknown, token: string | null = null) => {
    failedQueue.forEach((prom) => {
        if (token) {
            prom.resolve(token);
        } else {
            prom.reject(error);
        }
    });
    failedQueue = [];
};

function clearAuthState() {
    localStorage.removeItem("token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("user");
    localStorage.removeItem("current_team_id");
    localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
    window.dispatchEvent(new Event(ROADMAP_POLLING_CLEARED_EVENT));
    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
}

// --- Interceptors ---

apiClient.interceptors.request.use((config) => {
    if (typeof window === "undefined") {
        return config;
    }

    const token = localStorage.getItem("token");
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }

    const teamId = localStorage.getItem("current_team_id");
    if (teamId) {
        config.headers["X-Team-Id"] = teamId;
    }

    return config;
});

apiClient.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
        if (typeof window === "undefined") {
            return Promise.reject(error);
        }

        const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
        if (!originalRequest) {
            return Promise.reject(error);
        }

        // Only handle 401 when user had a token (not guest)
        if (error.response?.status !== 401 || !localStorage.getItem("token")) {
            return Promise.reject(error);
        }

        // Prevent infinite retry loop
        if (originalRequest._retry) {
            clearAuthState();
            return Promise.reject(error);
        }

        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken) {
            clearAuthState();
            return Promise.reject(error);
        }

        // If already refreshing, queue this request
        if (isRefreshing) {
            return new Promise((resolve, reject) => {
                failedQueue.push({
                    resolve: (newToken: string) => {
                        originalRequest.headers.Authorization = `Bearer ${newToken}`;
                        originalRequest._retry = true;
                        resolve(apiClient(originalRequest));
                    },
                    reject,
                });
            });
        }

        isRefreshing = true;
        originalRequest._retry = true;

        try {
            // Use raw axios to avoid interceptor recursion.
            // Retry up to 3 times on network errors (no server response),
            // but fail immediately on server rejection (4xx/5xx).
            const MAX_REFRESH_RETRIES = 3;
            let lastError: unknown = null;

            for (let attempt = 0; attempt < MAX_REFRESH_RETRIES; attempt++) {
                try {
                    const response = await axios.post(`${baseURL}/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token: newRefreshToken } = response.data;

                    localStorage.setItem("token", access_token);
                    localStorage.setItem("refresh_token", newRefreshToken);
                    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));

                    processQueue(null, access_token);
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return apiClient(originalRequest);
                } catch (err) {
                    lastError = err;
                    const axiosErr = err as AxiosError;
                    // Server responded with an error (token invalid/expired) → no retry
                    if (axiosErr.response) {
                        break;
                    }
                    // Network error (no response) → retry after short delay
                    if (attempt < MAX_REFRESH_RETRIES - 1) {
                        await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
                    }
                }
            }

            // All retries exhausted or server rejected — log out
            processQueue(lastError, null);
            clearAuthState();
            return Promise.reject(lastError);
        } finally {
            isRefreshing = false;
        }
    }
);

// --- Proactive Token Refresh ---
// Parses JWT exp claim and schedules a background refresh before expiry.

let proactiveRefreshTimer: ReturnType<typeof setTimeout> | null = null;

function parseJwtExp(token: string): number | null {
    try {
        const parts = token.split(".");
        if (parts.length !== 3) return null;
        const payload = JSON.parse(atob(parts[1]));
        return typeof payload.exp === "number" ? payload.exp : null;
    } catch {
        return null;
    }
}

function scheduleProactiveRefresh() {
    if (typeof window === "undefined") return;
    if (proactiveRefreshTimer) {
        clearTimeout(proactiveRefreshTimer);
        proactiveRefreshTimer = null;
    }

    const token = localStorage.getItem("token");
    if (!token) return;

    const exp = parseJwtExp(token);
    if (!exp) return;

    const expiresAtMs = exp * 1000;
    const delayMs = expiresAtMs - Date.now() - PROACTIVE_REFRESH_MARGIN_MS;
    if (delayMs <= 0) return; // already within margin or expired

    proactiveRefreshTimer = setTimeout(async () => {
        proactiveRefreshTimer = null;
        const refreshToken = localStorage.getItem("refresh_token");
        if (!refreshToken || isRefreshing) return;

        try {
            const response = await axios.post(`${baseURL}/auth/refresh`, {
                refresh_token: refreshToken,
            });
            const { access_token, refresh_token: newRefreshToken } = response.data;
            localStorage.setItem("token", access_token);
            localStorage.setItem("refresh_token", newRefreshToken);
            window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
        } catch {
            // Proactive refresh failed silently — the 401 interceptor will handle it
        }
    }, delayMs);
}

// Re-schedule whenever auth state changes (login, silent refresh, etc.)
if (typeof window !== "undefined") {
    window.addEventListener(AUTH_STORAGE_EVENT, scheduleProactiveRefresh);
    scheduleProactiveRefresh();
}
