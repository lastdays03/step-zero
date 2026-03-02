export type TemplateStatus = "DRAFT" | "REVIEW" | "APPROVED" | "ARCHIVED";

export interface RoadmapTemplateAction {
  id: number;
  template_step_id: number;
  action_type: "CHECKLIST" | "LEGAL_BASIS" | "DOCUMENT";
  title: string;
  description: string;
  source_url: string | null;
  actionkit_item_id: number | null;
  actionkit_file_id: number | null;
  sort_order: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

export interface RoadmapTemplateStep {
  id: number;
  template_id: number;
  step_order: number;
  phase: string;
  title: string;
  objective: string;
  estimated_days: number;
  risk_notes: string[];
  created_at: string;
  actions: RoadmapTemplateAction[];
}

export interface RoadmapTemplate {
  id: number;
  business_type: string;
  startup_method: string | null;
  startup_type: string | null;
  title: string;
  status: TemplateStatus;
  version: number;
  source_roadmap_id: string | null;
  created_by: number;
  approved_by: number | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface RoadmapTemplateDetail extends RoadmapTemplate {
  steps: RoadmapTemplateStep[];
}

export interface TemplateSummary {
  total: number;
  draft: number;
  review: number;
  approved: number;
  archived: number;
}

export interface RoadmapSearchResult {
  id: string;
  title: string;
  business_type: string;
  startup_method: string | null;
  startup_type: string | null;
  created_at: string;
}
