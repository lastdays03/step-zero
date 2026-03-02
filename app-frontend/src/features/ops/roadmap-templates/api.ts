import { apiClient } from "@/lib/api-client";

import type {
  RoadmapSearchResult,
  RoadmapTemplate,
  RoadmapTemplateAction,
  RoadmapTemplateDetail,
  RoadmapTemplateStep,
  TemplateSummary,
} from "./types";

/** GET /ops/roadmap-templates/summary */
export async function fetchTemplateSummary(): Promise<TemplateSummary> {
  const { data } = await apiClient.get<TemplateSummary>(
    "/ops/roadmap-templates/summary",
  );
  return data;
}

/** GET /ops/roadmap-templates */
export async function fetchTemplates(params?: {
  status?: string;
  business_type?: string;
}): Promise<RoadmapTemplate[]> {
  const { data } = await apiClient.get<RoadmapTemplate[]>(
    "/ops/roadmap-templates",
    { params },
  );
  return data;
}

/** GET /ops/roadmap-templates/:id */
export async function fetchTemplateDetail(
  id: number,
): Promise<RoadmapTemplateDetail> {
  const { data } = await apiClient.get<RoadmapTemplateDetail>(
    `/ops/roadmap-templates/${id}`,
  );
  return data;
}

/** POST /ops/roadmap-templates/from-roadmap */
export async function createTemplateFromRoadmap(
  roadmapId: string,
): Promise<RoadmapTemplate> {
  const { data } = await apiClient.post<RoadmapTemplate>(
    "/ops/roadmap-templates/from-roadmap",
    { roadmap_id: roadmapId },
  );
  return data;
}

/** PATCH /ops/roadmap-templates/:id */
export async function updateTemplate(
  id: number,
  payload: { title?: string; business_type?: string; startup_method?: string; startup_type?: string },
): Promise<RoadmapTemplate> {
  const { data } = await apiClient.patch<RoadmapTemplate>(
    `/ops/roadmap-templates/${id}`,
    payload,
  );
  return data;
}

/** PATCH /ops/roadmap-templates/:id/status */
export async function updateTemplateStatus(
  id: number,
  payload: { new_status: string; reason?: string },
): Promise<RoadmapTemplate> {
  const { data } = await apiClient.patch<RoadmapTemplate>(
    `/ops/roadmap-templates/${id}/status`,
    payload,
  );
  return data;
}

/** DELETE /ops/roadmap-templates/:id */
export async function deleteTemplate(id: number): Promise<void> {
  await apiClient.delete(`/ops/roadmap-templates/${id}`);
}

/** POST /ops/roadmap-templates/:templateId/steps/:stepId/actions */
export async function createTemplateAction(
  templateId: number,
  stepId: number,
  payload: {
    action_type: string;
    title: string;
    description?: string;
    source_url?: string;
  },
): Promise<RoadmapTemplateAction> {
  const { data } = await apiClient.post<RoadmapTemplateAction>(
    `/ops/roadmap-templates/${templateId}/steps/${stepId}/actions`,
    payload,
  );
  return data;
}

/** PATCH /ops/roadmap-templates/:templateId/steps/:stepId/actions/:actionId */
export async function updateTemplateAction(
  templateId: number,
  stepId: number,
  actionId: number,
  payload: Record<string, unknown>,
): Promise<RoadmapTemplateAction> {
  const { data } = await apiClient.patch<RoadmapTemplateAction>(
    `/ops/roadmap-templates/${templateId}/steps/${stepId}/actions/${actionId}`,
    payload,
  );
  return data;
}

/** DELETE /ops/roadmap-templates/:templateId/steps/:stepId/actions/:actionId */
export async function deleteTemplateAction(
  templateId: number,
  stepId: number,
  actionId: number,
): Promise<void> {
  await apiClient.delete(
    `/ops/roadmap-templates/${templateId}/steps/${stepId}/actions/${actionId}`,
  );
}

// ── Step CRUD ──

/** POST /ops/roadmap-templates/:templateId/steps */
export async function createTemplateStep(
  templateId: number,
  payload: {
    phase?: string;
    title: string;
    objective?: string;
    estimated_days?: number;
    risk_notes?: string[];
  },
): Promise<RoadmapTemplateStep> {
  const { data } = await apiClient.post<RoadmapTemplateStep>(
    `/ops/roadmap-templates/${templateId}/steps`,
    payload,
  );
  return data;
}

/** PATCH /ops/roadmap-templates/:templateId/steps/:stepId */
export async function updateTemplateStep(
  templateId: number,
  stepId: number,
  payload: {
    phase?: string;
    title?: string;
    objective?: string;
    estimated_days?: number;
    risk_notes?: string[];
  },
): Promise<RoadmapTemplateStep> {
  const { data } = await apiClient.patch<RoadmapTemplateStep>(
    `/ops/roadmap-templates/${templateId}/steps/${stepId}`,
    payload,
  );
  return data;
}

/** DELETE /ops/roadmap-templates/:templateId/steps/:stepId */
export async function deleteTemplateStep(
  templateId: number,
  stepId: number,
): Promise<void> {
  await apiClient.delete(
    `/ops/roadmap-templates/${templateId}/steps/${stepId}`,
  );
}

/** PATCH /ops/roadmap-templates/:templateId/steps/reorder */
export async function reorderTemplateSteps(
  templateId: number,
  stepIds: number[],
): Promise<RoadmapTemplateStep[]> {
  const { data } = await apiClient.patch<RoadmapTemplateStep[]>(
    `/ops/roadmap-templates/${templateId}/steps/reorder`,
    { step_ids: stepIds },
  );
  return data;
}

// ── Roadmap search ──

/** GET /ops/roadmap-templates/roadmaps/search */
export async function searchRoadmaps(params?: {
  business_type?: string;
  startup_method?: string;
  startup_type?: string;
  q?: string;
}): Promise<RoadmapSearchResult[]> {
  const { data } = await apiClient.get<RoadmapSearchResult[]>(
    "/ops/roadmap-templates/roadmaps/search",
    { params },
  );
  return data;
}
