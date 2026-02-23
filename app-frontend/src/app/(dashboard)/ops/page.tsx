"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/providers/AuthProvider";

export default function OpsPage() {
    const router = useRouter();
    const { isLoggedIn, isAuthReady, canAccessOps } = useAuth();

    useEffect(() => {
        if (!isAuthReady) return;
        if (!isLoggedIn) {
            router.replace("/login");
            return;
        }
        if (!canAccessOps) {
            router.replace("/dashboard");
        }
    }, [canAccessOps, isAuthReady, isLoggedIn, router]);

    if (!isAuthReady || !isLoggedIn || !canAccessOps) {
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-6">
                <p className="text-sm text-slate-600">권한을 확인하는 중입니다...</p>
            </section>
        );
    }

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
                    <h2 className="text-base font-semibold text-slate-900">사용자 관리</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        최근 가입자 조회, 운영자 권한 대상 확인
                    </p>
                    <Link href="/ops/users" className="mt-4 inline-block text-sm font-semibold text-blue-600">
                        열기
                    </Link>
                </article>
                <article className="rounded-2xl border border-slate-200 bg-white p-5">
                    <h2 className="text-base font-semibold text-slate-900">그로스 클럽 관리</h2>
                    <p className="mt-1 text-sm text-slate-600">
                        신고 콘텐츠 검토 및 블라인드/해제 운영
                    </p>
                    <Link href="/ops/growth-club" className="mt-4 inline-block text-sm font-semibold text-blue-600">
                        열기
                    </Link>
                </article>
            </div>
        </section>
    );
}
