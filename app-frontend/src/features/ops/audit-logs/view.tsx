"use client";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

export function OpsAuditLogsView() {
  const { canRender } = useOpsAccessGuard();

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <header>
        <h1 className="text-xl font-bold text-slate-900">운영 감사로그</h1>
        <p className="mt-2 text-sm text-slate-600">운영자 조치 로그를 조회하고 추적하는 화면입니다.</p>
      </header>
      <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
        구현 예정: 필터 조회, 로그 목록, 변경 전/후 상세 패널.
      </div>
    </section>
  );
}
