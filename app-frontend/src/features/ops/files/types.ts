export type OpsFile = {
  id: number;
  owner_type: string;
  owner_id: number;
  category: string;
  object_key: string;
  original_filename: string | null;
  mime_type: string | null;
  size_bytes: number | null;
  kind: string | null;
  uploaded_at: string | null;
  public_url: string;
};

export type OpsFileListResponse = {
  data: OpsFile[];
  total: number;
  page: number;
  page_size: number;
};

export type OpsFileListParams = {
  page?: number;
  page_size?: number;
  sort_by?: "created_at" | "uploaded_at" | "size_bytes" | "original_filename";
  sort_dir?: "asc" | "desc";
  owner_type?: string;
  mime_group?: "image" | "document" | "other";
  date_from?: string;
  date_to?: string;
  search?: string;
};

export type OpsFileStatsGroupItem = {
  owner_type?: string;
  mime_group?: string;
  count: number;
  bytes: number;
};

export type OpsFileStats = {
  total_files: number;
  total_bytes: number;
  by_owner_type: OpsFileStatsGroupItem[];
  by_mime_group: OpsFileStatsGroupItem[];
};

export type OpsFileBatchDeleteResponse = {
  deleted: number;
  failed: number;
};
