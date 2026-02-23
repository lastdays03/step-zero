/* eslint-disable */
/* AUTO-GENERATED FILE. DO NOT EDIT. */
/* Generated from app-backend/openapi.json */

export type Body_login_access_token_api_v1_auth_login_post = {
  "grant_type"?: string | unknown;
  "username": string;
  "password": string;
  "scope"?: string;
  "client_id"?: string | unknown;
  "client_secret"?: string | unknown;
};

export type Body_login_access_token_api_v2_auth_login_post = {
  "grant_type"?: string | unknown;
  "username": string;
  "password": string;
  "scope"?: string;
  "client_id"?: string | unknown;
  "client_secret"?: string | unknown;
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

export type GenerationRequest = {
  "business_type": string;
  "location": string;
  "description": string;
};

export type GenerationResponse = {
  "roadmap_id": string;
  "title": string;
  "steps": RoadmapStepResponse[];
};

export type GoogleLoginRequest = {
  "id_token": string;
};

export type GrowthClub = {
  "founders_online": number;
};

export type HTTPValidationError = {
  "detail"?: ValidationError[];
};

export type RagQueryRequest = {
  "question": string;
};

export type RagQueryResponse = {
  "answer": string;
};

export type RoadmapCreateRequest = {
  "business_type": string;
  "location": string;
  "description": string;
};

export type RoadmapItem = {
  "title": string;
  "status": string;
  "date": string;
};

export type RoadmapResponse = {
  "roadmap_id": string;
  "title": string;
  "steps": RoadmapStepResponse[];
};

export type RoadmapStepResponse = {
  "id": number;
  "title": string;
  "status": string;
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

export type TokenWithUser = {
  "access_token": string;
  "token_type": string;
  "user": UserRead;
};

export type UserRead = {
  "email": string;
  "full_name"?: string | unknown;
  "is_active"?: boolean;
  "is_superuser"?: boolean;
  "id": number;
};

export type ValidationError = {
  "loc": string | number[];
  "msg": string;
  "type": string;
  "input"?: unknown;
  "ctx"?: {

};
};
