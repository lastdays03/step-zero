"use client";

import { use } from "react";

import { TemplateDetailView } from "@/features/ops/roadmap-templates";

export default function OpsRoadmapTemplateDetailPage({
  params,
}: {
  params: Promise<{ templateId: string }>;
}) {
  const { templateId } = use(params);
  return <TemplateDetailView templateId={Number(templateId)} />;
}
