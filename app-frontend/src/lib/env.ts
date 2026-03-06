const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export function getApiBaseUrl(): string {
  return (
    explicitBaseUrl ||
    (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1")
  );
}

export function getApiHost(): string {
  return (
    apiUrl?.replace(/\/$/, "") ||
    explicitBaseUrl?.replace(/\/api\/v1\/?$/, "") ||
    "http://localhost:8000"
  );
}
