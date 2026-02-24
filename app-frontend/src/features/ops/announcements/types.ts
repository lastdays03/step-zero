export type OpsAnnouncementStatus = "draft" | "published" | "archived";

export interface OpsAnnouncement {
    id: number;
    title: string;
    content: string;
    status: OpsAnnouncementStatus;
    admin_id: number;
    published_at: string | null;
    created_at: string;
    updated_at: string;
}

export interface OpsAnnouncementList {
    items: OpsAnnouncement[];
    total: number;
}
