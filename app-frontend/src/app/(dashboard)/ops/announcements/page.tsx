"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuth } from "@/providers/AuthProvider";

export default function OpsAnnouncementsPage() {
    const router = useRouter();
    const { isLoggedIn, isAuthReady, canAccessOps } = useAuth();

    useEffect(() => {
        if (!isAuthReady) return;
        if (!isLoggedIn) {
            router.replace("/dashboard");
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
                <h1 className="text-xl font-bold text-slate-900">공지 관리</h1>
                <p className="mt-2 text-sm text-slate-600">
                    공지 작성/수정/게시/내림 운영을 위한 화면입니다.
                </p>
            </header>
            <div className="rounded-xl bg-slate-50 p-4 text-sm text-slate-600">
                구현 예정: 공지 목록, 작성/수정 에디터, 게시/내림 상태 전환.
            </div>
        </section>
    );
}
