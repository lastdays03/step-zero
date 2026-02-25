export type OpsAnnouncementStatus = "draft" | "published" | "archived";

export interface OpsAnnouncement {
  id: number;
  title: string;
  content: string;
  status: OpsAnnouncementStatus;
  created_by: number;
  updated_by: number;
  created_at: string;
  updated_at: string;
}

export interface OpsAnnouncementList {
  items: OpsAnnouncement[];
}
