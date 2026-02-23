import axios, { AxiosError, InternalAxiosRequestConfig } from "axios";

const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
export const AUTH_STORAGE_EVENT = "auth-storage-changed";
export const ROADMAP_POLLING_CLEARED_EVENT = "roadmap-polling-cleared";
const ROADMAP_JOB_STORAGE_KEY = "roadmap_polling_job_id";

const baseURL = explicitBaseUrl
    || (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1");

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
            // Use raw axios to avoid interceptor recursion
            const response = await axios.post(`${baseURL}/auth/refresh`, {
                refresh_token: refreshToken,
            });

            const { access_token, refresh_token: newRefreshToken } = response.data;

            localStorage.setItem("token", access_token);
            localStorage.setItem("refresh_token", newRefreshToken);
            window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));

            // Retry original request + queued requests
            processQueue(null, access_token);
            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return apiClient(originalRequest);
        } catch (refreshError) {
            // Refresh failed — clear everything and log out
            processQueue(refreshError, null);
            clearAuthState();
            return Promise.reject(refreshError);
        } finally {
            isRefreshing = false;
        }
    }
);
