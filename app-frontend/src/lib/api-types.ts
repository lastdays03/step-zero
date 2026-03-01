/* eslint-disable */
/* AUTO-GENERATED FILE. DO NOT EDIT. */
/* Generated from app-backend/openapi.json */

export type ActionKitCategory = {
  "title": string;
  "items": ActionKitItem[];
};

export type ActionKitCategoryCreateRequest = {
  "domain"?: string;
  "slug": string;
  "title": string;
  "sort_order"?: number;
  "is_active"?: boolean;
};

export type ActionKitCategoryResponse = {
  "id": number;
  "domain": string;
  "slug": string;
  "title": string;
  "sort_order": number;
  "is_active": boolean;
};

export type ActionKitCategoryUpdateRequest = {
  "slug"?: string | unknown;
  "title"?: string | unknown;
  "sort_order"?: number | unknown;
  "is_active"?: boolean | unknown;
};

export type ActionKitChecklistResponse = {
  "id": number;
  "content": string;
  "sort_order": number;
};

export type ActionKitFileResponse = {
  "id": number;
  "version": number;
  "original_filename": string | unknown;
  "mime_type": string | unknown;
  "size_bytes": number | unknown;
  "is_current": boolean;
  "uploaded_at": string;
};

export type ActionKitFileUploadResponse = {
  "item_id": number;
  "file_id": number;
  "version": number;
  "object_key": string;
  "download_url": string;
  "original_filename"?: string | unknown;
  "mime_type"?: string | unknown;
  "size_bytes"?: number | unknown;
  "checksum"?: string | unknown;
};

export type ActionKitItem = {
  "id"?: number | unknown;
  "tag"?: string | unknown;
  "name": string;
  "summary": string;
  "type": string;
  "path": string;
  "relatedLaws"?: string | RelatedLaw[] | unknown;
  "highlights"?: Highlight[] | unknown;
  "complianceChecklist"?: string[] | unknown;
  "dday"?: string | unknown;
};

export type ActionKitItemCreateRequest = {
  "domain": string;
  "category_id": number;
  "name": string;
  "summary": string;
  "tag"?: string | unknown;
  "ext"?: string | unknown;
  "size_label"?: string | unknown;
  "file_type"?: string | unknown;
  "dday"?: string | unknown;
  "sort_order"?: number;
  "is_active"?: boolean;
};

export type ActionKitItemHighlightResponse = {
  "id": number;
  "content": string;
  "sort_order": number;
};

export type ActionKitItemOrderUpdate = {
  "id": number;
  "sort_order": number;
};

export type ActionKitItemReorderRequest = {
  "items": ActionKitItemOrderUpdate[];
};

export type ActionKitItemResponse = {
  "id": number;
  "domain": string;
  "category_id": number;
  "name": string;
  "summary": string;
  "tag": string | unknown;
  "ext": string | unknown;
  "size_label": string | unknown;
  "file_type": string | unknown;
  "dday": string | unknown;
  "sort_order": number;
  "is_active": boolean;
  "created_at": string;
  "updated_at": string;
  "files"?: ActionKitFileResponse[];
  "related_laws"?: RelatedLawResponse[];
  "highlights"?: ActionKitItemHighlightResponse[];
  "checklists"?: ActionKitChecklistResponse[];
};

export type ActionKitItemUpdateRequest = {
  "category_id"?: number | unknown;
  "name"?: string | unknown;
  "summary"?: string | unknown;
  "tag"?: string | unknown;
  "ext"?: string | unknown;
  "size_label"?: string | unknown;
  "file_type"?: string | unknown;
  "dday"?: string | unknown;
  "sort_order"?: number | unknown;
  "is_active"?: boolean | unknown;
};

export type AnnouncementCreate = {
  "title": string;
  "content": string;
};

export type AnnouncementItem = {
  "id": number;
  "title": string;
  "content": string;
  "status": "draft" | "published" | "archived";
  "created_by": number;
  "updated_by": number;
  "created_at": string;
  "published_at"?: string | unknown;
  "updated_at": string;
};

export type AnnouncementList = {
  "items": AnnouncementItem[];
};

export type AnnouncementStatusUpdate = {
  "status": "draft" | "published" | "archived";
  "audit_log_reason"?: string | unknown;
};

export type AnnouncementUpdate = {
  "title"?: string | unknown;
  "content"?: string | unknown;
};

export type AuthorRead = {
  "id": number;
  "full_name"?: string | unknown;
  "email"?: string | unknown;
  "username"?: string | unknown;
  "nickname"?: string | unknown;
  "profile_img"?: string | unknown;
  "is_public"?: boolean;
  "neighborhood"?: string | unknown;
  "industry"?: string | unknown;
  "is_suspended"?: boolean;
  "suspended_at"?: string | unknown;
};

export type Body_create_post_api_v1_community_posts_post = {
  "title": string;
  "content": string;
  "category"?: string;
  "images"?: string[];
  "files"?: string[];
};

export type Body_create_post_api_v1_growth_club_posts_post = {
  "title": string;
  "content": string;
  "category"?: string;
  "images"?: string[];
  "files"?: string[];
};

export type Body_login_access_token_api_v1_auth_login_post = {
  "grant_type"?: string | unknown;
  "username": string;
  "password": string;
  "scope"?: string;
  "client_id"?: string | unknown;
  "client_secret"?: string | unknown;
};

export type Body_upload_actionkit_file_api_v1_actionkits_items__item_id__files_post = {
  "upload": string;
};

export type Body_upload_actionkit_item_file_api_v1_ops_actionkit_items__item_id__files_post = {
  "file": string;
};

export type Body_upload_my_profile_image_api_v1_profile_me_image_post = {
  "file": string;
};

export type BulkStatusUpdateRequest = {
  "user_ids": number[];
  "status": string;
  "reason": string;
  "duration_days"?: number | unknown;
};

export type ChatRequest = {
  "message": string;
};

export type ChatResponse = {
  "answer": string;
  "source": string;
};

export type ChecklistRequest = {
  "content": string;
};

export type CommentCreate = {
  "content": string;
  "post_id": number;
  "parent_id"?: number | unknown;
};

export type CurrentPhase = {
  "title": string;
  "progress": number;
  "status": string;
};

export type DashboardResponse = {
  "user_name": string;
  "current_phase": CurrentPhase;
  "roadmap": RoadmapItem[];
  "stats": DashboardStats;
  "growth_club": GrowthClub;
};

export type DashboardStats = {
  "days_left": number;
  "tasks_completed": number;
  "total_tasks": number;
};

export type DisciplineHistoryRead = {
  "id": number;
  "user_id": number;
  "admin_id": number;
  "prev_status": string;
  "new_status": string;
  "reason": string;
  "suspended_until"?: string | unknown;
  "created_at": string;
};

export type GoogleLoginRequest = {
  "id_token": string;
};

export type GrowthClub = {
  "founders_online": number;
};

export type GrowthClubAttachmentRead = {
  "id": number;
  "kind": string;
  "object_key": string;
  "original_filename"?: string | unknown;
  "mime_type"?: string | unknown;
  "size_bytes"?: number | unknown;
  "created_at": string;
};

export type GrowthClubCommentRead = {
  "content": string;
  "post_id": number;
  "parent_id"?: number | unknown;
  "id": number;
  "author_id": number;
  "created_at": string;
  "author": AuthorRead;
  "report_count"?: number;
  "report_reason"?: string | unknown;
};

export type GrowthClubPostRead = {
  "title": string;
  "content": string;
  "category": string;
  "neighborhood"?: string | unknown;
  "industry"?: string | unknown;
  "id": number;
  "author_id": number;
  "created_at": string;
  "author": AuthorRead;
  "comments"?: GrowthClubCommentRead[];
  "attachments"?: GrowthClubAttachmentRead[];
  "report_count": number;
  "report_reason"?: string | unknown;
  "likes_count"?: number;
  "is_liked"?: boolean;
};

export type HTTPValidationError = {
  "detail"?: ValidationError[];
};

export type Highlight = {
  "id": number;
  "content": string;
};

export type HighlightRequest = {
  "content": string;
};

export type LawChapter = {
  "title": string;
  "items": LawItem[];
};

export type LawItem = {
  "name": string;
  "ext": string;
  "size": string;
  "summary": string;
  "path": string;
  "highlights"?: string[] | unknown;
};

export type NotificationRead = {
  "user_id": number;
  "content": string;
  "type": string;
  "link"?: string | unknown;
  "is_read"?: boolean;
  "is_deleted"?: boolean;
  "resource_id"?: number | unknown;
  "id": number;
  "created_at": string;
};

export type OpsActionKitItemStatusUpdateRequest = {
  "is_active": boolean;
  "reason"?: string | unknown;
};

export type OpsUserRead = {
  "id": number;
  "email": string;
  "full_name": string | unknown;
  "status": string;
  "report_count": number;
  "last_login_at": string | unknown;
  "is_active": boolean;
  "is_superuser": boolean;
  "suspended_until"?: string | unknown;
  "created_at": string;
};

export type RagQueryRequest = {
  "question": string;
};

export type RagQueryResponse = {
  "answer": string;
};

export type RefreshTokenRequest = {
  "refresh_token": string;
};

export type RelatedLaw = {
  "name": string;
  "summary"?: string | unknown;
};

export type RelatedLawRequest = {
  "law_name": string;
  "law_summary"?: string | unknown;
};

export type RelatedLawResponse = {
  "id": number;
  "law_name": string;
  "law_summary": string | unknown;
  "sort_order": number;
};

export type ReportRequest = {
  "reason": string;
};

export type RoadmapCreateRequest = {
  "business_type": string;
  "location": string;
  "description"?: string;
  "startup_type"?: string | unknown;
  "startup_method"?: string | unknown;
  "open_timeline"?: string | unknown;
  "budget_range"?: string | unknown;
  "additional_notes"?: string;
  "goal_horizon_days"?: number;
  "experience_level"?: string;
};

export type RoadmapDetailResponse = {
  "roadmap_id": string;
  "title": string;
  "created_at": string;
  "steps": RoadmapDetailStepResponse[];
};

export type RoadmapDetailStepResponse = {
  "id": number;
  "title": string;
  "status": string;
  "completed_at"?: string | unknown;
  "detail"?: RoadmapStepDetailResponse | unknown;
};

export type RoadmapInputValidateRequest = {
  "business_type": string;
  "location": string;
  "description"?: string;
};

export type RoadmapInputValidateResponse = {
  "valid": boolean;
  "normalized_business_type"?: string | unknown;
  "normalized_location"?: string | unknown;
  "reason"?: string | unknown;
  "confidence"?: number;
};

export type RoadmapItem = {
  "title": string;
  "status": string;
  "date": string;
};

export type RoadmapJobCreateRequest = {
  "business_type": string;
  "location": string;
  "description"?: string;
  "startup_type"?: string | unknown;
  "startup_method"?: string | unknown;
  "open_timeline"?: string | unknown;
  "budget_range"?: string | unknown;
  "additional_notes"?: string;
  "goal_horizon_days"?: number;
  "experience_level"?: string;
};

export type RoadmapJobResponse = {
  "job_id": string;
  "status": string;
  "stage": string;
  "progress": number;
  "roadmap_id"?: string | unknown;
  "error_code"?: string | unknown;
  "error_message"?: string | unknown;
};

export type RoadmapJobResultResponse = {
  "job_id": string;
  "status": string;
  "roadmap_id"?: string | unknown;
};

export type RoadmapListResponse = {
  "items": RoadmapSummaryItem[];
  "total": number;
};

export type RoadmapResponse = {
  "roadmap_id": string;
  "title": string;
  "steps": RoadmapStepResponse[];
};

export type RoadmapStepActionResponse = {
  "id": number;
  "action_type": string;
  "title": string;
  "description": string;
  "source_url"?: string | unknown;
  "metadata_json"?: {
  [key: string]: unknown;
};
};

export type RoadmapStepActionUpdateRequest = {
  "completed": boolean;
};

export type RoadmapStepDetailResponse = {
  "id": number;
  "phase": string;
  "objective": string;
  "estimated_days": number;
  "risk_notes": string[];
  "generation_mode": string;
  "source_count"?: number | unknown;
  "has_fallback"?: boolean | unknown;
  "mapping_source"?: string | unknown;
  "actions": RoadmapStepActionResponse[];
};

export type RoadmapStepResponse = {
  "id": number;
  "title": string;
  "status": string;
};

export type RoadmapStepStatusUpdateRequest = {
  "status": string;
};

export type RoadmapSummaryItem = {
  "roadmap_id": string;
  "title": string;
  "business_type": string;
  "location": string;
  "created_at": string;
  "progress": number;
  "total_steps": number;
  "completed_steps": number;
};

export type RoadmapUpdateRequest = {
  "title": string;
};

export type SuspendRequest = {
  "reason": string;
  "target_type": string;
  "target_id": number;
};

export type TeamRead = {
  "id": string;
  "name": string;
};

export type TokenWithTeams = {
  "access_token": string;
  "refresh_token": string;
  "token_type": string;
  "user": UserRead;
  "current_team_id": string;
  "teams": TeamRead[];
};

export type UserProfileRead = {
  "nickname"?: string | unknown;
  "profile_img"?: string | unknown;
  "is_public"?: boolean;
  "category"?: string | unknown;
  "region"?: string | unknown;
  "philosophy"?: string | unknown;
  "experiences"?: string[];
  "awards"?: string[];
  "certificates"?: string[];
  "id": number;
  "user_id": number;
  "updated_at": string;
  "completeness_rate": number;
  "full_name"?: string | unknown;
  "email"?: string | unknown;
};

export type UserProfileUpdate = {
  "nickname"?: string | unknown;
  "profile_img"?: string | unknown;
  "is_public"?: boolean;
  "category"?: string | unknown;
  "region"?: string | unknown;
  "philosophy"?: string | unknown;
  "experiences"?: string[];
  "awards"?: string[];
  "certificates"?: string[];
  "full_name"?: string | unknown;
};

export type UserRead = {
  "email": string;
  "full_name"?: string | unknown;
  "is_active"?: boolean;
  "is_superuser"?: boolean;
  "is_suspended"?: boolean;
  "suspended_at"?: string | unknown;
  "suspension_reason"?: string | unknown;
  "id": number;
};

export type UserStatusUpdateRequest = {
  "status": string;
  "reason": string;
  "duration_days"?: number | unknown;
};

export type ValidationError = {
  "loc": string | number[];
  "msg": string;
  "type": string;
  "input"?: unknown;
  "ctx"?: {

};
};
