"use client";

import type { TemplateStatus } from "../types";

const STATUS_CONFIG: Record<
  TemplateStatus,
  { label: string; className: string }
> = {
  DRAFT: {
    label: "초안",
    className: "bg-slate-100 text-slate-600",
  },
  REVIEW: {
    label: "검토중",
    className: "bg-amber-100 text-amber-700",
  },
  APPROVED: {
    label: "승인",
    className: "bg-emerald-100 text-emerald-700",
  },
  ARCHIVED: {
    label: "보관",
    className: "bg-gray-100 text-gray-500",
  },
};

export function TemplateStatusBadge({ status }: { status: TemplateStatus }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG.DRAFT;
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-bold ${config.className}`}
    >
      {config.label}
    </span>
  );
}
