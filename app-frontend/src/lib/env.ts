export function getApiBaseUrl(): string {
  const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || undefined;
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() || undefined;

  return (
    explicitBaseUrl ||
    (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1")
  );
}

export function getApiHost(): string {
  const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim() || undefined;
  const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim() || undefined;

  return (
    apiUrl?.replace(/\/$/, "") ||
    explicitBaseUrl?.replace(/\/api\/v1\/?$/, "") ||
    "http://localhost:8000"
  );
}
