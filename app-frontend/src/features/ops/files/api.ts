import { apiClient } from "@/lib/api-client";

import type {
  OpsFileBatchDeleteResponse,
  OpsFileListParams,
  OpsFileListResponse,
  OpsFileStats,
} from "./types";

export async function fetchFiles(
  params: OpsFileListParams = {},
): Promise<OpsFileListResponse> {
  const response = await apiClient.get("/ops/files/", { params });
  return response.data as OpsFileListResponse;
}

export async function fetchFileStats(): Promise<OpsFileStats> {
  const response = await apiClient.get("/ops/files/stats");
  return response.data as OpsFileStats;
}

export async function deleteFile(id: number): Promise<void> {
  await apiClient.delete(`/ops/files/${id}`);
}

export async function deleteFiles(
  ids: number[],
): Promise<OpsFileBatchDeleteResponse> {
  const response = await apiClient.delete("/ops/files/batch", {
    data: { ids },
  });
  return response.data as OpsFileBatchDeleteResponse;
}
