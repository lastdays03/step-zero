"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/providers/AuthProvider";

export default function OpsGrowthClubPage() {
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
