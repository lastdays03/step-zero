import axios from "axios";

const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

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
