"use client";

import Link from "next/link";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

export function OpsActionKitView() {
  const { canRender } = useOpsAccessGuard();

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6">
      <header>
        <h1 className="text-xl font-bold text-slate-900">액션 키트 관리</h1>
        <p className="mt-2 text-sm text-slate-600">
          액션 키트 라이브러리 운영, 업로드 정책 점검, 카테고리 품질 검토를 위한 운영 화면입니다.
        </p>
      </header>
      <div className="space-y-3 rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
        <p>구현 예정: 업로드 승인 플로우, 카테고리/파일 품질 점검 대시보드, 변경 이력.</p>
        <Link href="/actionkit" className="inline-block font-semibold text-blue-600">사용자 액션 키트 화면 열기</Link>
      </div>
    </section>
  );
}
