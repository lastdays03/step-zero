import { getApiHost } from "@/lib/env";

export const resolveUploadUrl = (value?: string): string => {
  if (!value) return "";
  if (value.startsWith("http://") || value.startsWith("https://")) return value;

  // R2 모드: NEXT_PUBLIC_STORAGE_URL이 설정되어 있으면 사용
  const storageUrl = process.env.NEXT_PUBLIC_STORAGE_URL;
  if (storageUrl) {
    const normalized = value.replace(/^\/+/, "");
    return `${storageUrl.replace(/\/$/, "")}/${normalized}`;
  }

  // 로컬 모드: 기존 API 기반 URL
  const apiHost = getApiHost();

  const normalized = value
    .replace(/^\/+/, "")
    .replace(/^api\/(?:v1\/)?uploads\/?/, "");
  return `${apiHost}/api/uploads/${normalized}`;
};
