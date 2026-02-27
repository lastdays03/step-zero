"use client";

import Link from "next/link";

import { OpsAccessPlaceholder } from "@/features/ops/shared/ops-access-placeholder";
import { useOpsAccessGuard } from "@/features/ops/shared/use-ops-access-guard";

export function OpsHomeView() {
  const { canRender } = useOpsAccessGuard();

  if (!canRender) return <OpsAccessPlaceholder />;

  return (
    <section className="space-y-4">
      <header className="rounded-2xl border border-slate-200 bg-white p-6">
        <h1 className="text-xl font-bold text-slate-900">플랫폼 운영 콘솔</h1>
        <p className="mt-2 text-sm text-slate-600">
          플랫폼 운영자 전용 영역입니다. 사용자와 운영 지표를 관리합니다.
        </p>
      </header>
      <div className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">운영 리포트</h2>
          <p className="mt-1 text-sm text-slate-600">최근 7일 서비스 핵심 지표 확인</p>
          <Link href="/ops/reports" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">사용자 관리</h2>
          <p className="mt-1 text-sm text-slate-600">최근 가입자 조회, 운영자 권한 대상 확인</p>
          <Link href="/ops/users" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">그로스 클럽 관리</h2>
          <p className="mt-1 text-sm text-slate-600">신고 콘텐츠 검토 및 블라인드/해제 운영</p>
          <Link href="/ops/growth-club" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">액션 키트 관리</h2>
          <p className="mt-1 text-sm text-slate-600">문서 라이브러리 운영과 업로드 정책 점검</p>
          <Link href="/ops/actionkit" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">공지 관리</h2>
          <p className="mt-1 text-sm text-slate-600">공지 작성/수정/게시/내림 운영</p>
          <Link href="/ops/announcements" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
        <article className="rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-base font-semibold text-slate-900">운영 감사로그</h2>
          <p className="mt-1 text-sm text-slate-600">운영자 조치 이력 조회 및 추적</p>
          <Link href="/ops/audit-logs" className="mt-4 inline-block text-sm font-semibold text-blue-600">열기</Link>
        </article>
      </div>
    </section>
  );
}
