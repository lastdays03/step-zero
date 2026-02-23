import axios from "axios";

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
    (error) => {
        if (
            typeof window !== "undefined"
            && error?.response?.status === 401
            && localStorage.getItem("token")
        ) {
            localStorage.removeItem("token");
            localStorage.removeItem("user");
            localStorage.removeItem("current_team_id");
            localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
            window.dispatchEvent(new Event(ROADMAP_POLLING_CLEARED_EVENT));
            window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
        }
        return Promise.reject(error);
    }
);
