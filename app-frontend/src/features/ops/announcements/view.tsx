"use client";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

export function OpsAnnouncementsView() {
  const { canRender } = useOpsAccessGuard();

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <header>
        <h1 className="text-xl font-bold text-slate-900">공지 관리</h1>
        <p className="mt-2 text-sm text-slate-600">공지 작성/수정/게시/내림 운영을 위한 화면입니다.</p>
      </header>
      <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
        구현 예정: 공지 목록, 작성/수정 에디터, 게시/내림 상태 전환.
      </div>
    </section>
  );
}
