"use client";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

export function OpsGrowthClubView() {
  const { canRender } = useOpsAccessGuard();

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <header>
        <h1 className="text-xl font-bold text-slate-900">그로스 클럽 관리</h1>
        <p className="mt-2 text-sm text-slate-600">
          신고 게시글/댓글 검토, 블라인드/해제, 운영 조치를 관리하는 화면입니다.
        </p>
      </header>
      <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
        구현 예정: 신고 큐 조회, 콘텐츠 조치(블라인드/해제), 조치 이력.
      </div>
    </section>
  );
}
