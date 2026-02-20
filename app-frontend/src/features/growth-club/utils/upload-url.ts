const apiHost = (
    process.env.NEXT_PUBLIC_API_URL
    || process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/api\/v1\/?$/, "")
    || "http://localhost:8000"
).replace(/\/$/, "");

export const resolveUploadUrl = (value?: string): string => {
    if (!value) return "";
    if (value.startsWith("http://") || value.startsWith("https://")) return value;
    const normalized = value
        .replace(/^\/+/, "")
        .replace(/^api\/(?:v1\/)?uploads\/?/, "");
    return `${apiHost}/api/uploads/${normalized}`;
};
