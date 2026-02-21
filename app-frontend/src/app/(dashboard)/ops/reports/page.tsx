"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { apiClient } from "@/lib/api-client";
import { useAuth } from "@/providers/AuthProvider";

type OpsSummary = {
    active_users_7d: number;
    new_signups_7d: number;
    roadmaps_generated_7d: number;
    generated_at: string;
};

export default function OpsReportsPage() {
    const router = useRouter();
    const { isLoggedIn, isAuthReady, canAccessOps } = useAuth();
    const [summary, setSummary] = useState<OpsSummary | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!isAuthReady) return;
        if (!isLoggedIn) {
            router.replace("/dashboard");
            return;
        }
        if (!canAccessOps) {
            router.replace("/dashboard");
            return;
        }

        const load = async () => {
            try {
                const response = await apiClient.get("/ops/reports/summary");
                setSummary(response.data as OpsSummary);
            } catch (err) {
                setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
            } finally {
                setIsLoading(false);
            }
        };

        void load();
    }, [canAccessOps, isAuthReady, isLoggedIn, router]);

    if (!isAuthReady || isLoading) {
        return <p className="text-sm text-slate-600">운영 지표를 불러오는 중입니다...</p>;
    }
    if (error) {
        return <p className="text-sm text-red-600">{error}</p>;
    }
    if (!summary) {
        return <p className="text-sm text-slate-600">조회된 지표가 없습니다.</p>;
    }

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6">
            <h1 className="text-xl font-bold text-slate-900">운영 리포트</h1>
            <dl className="mt-4 grid gap-3 md:grid-cols-3">
                <div className="rounded-xl bg-slate-50 p-4">
                    <dt className="text-xs text-slate-500">최근 7일 활성 사용자</dt>
                    <dd className="mt-1 text-lg font-bold text-slate-900">{summary.active_users_7d}</dd>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                    <dt className="text-xs text-slate-500">최근 7일 가입자</dt>
                    <dd className="mt-1 text-lg font-bold text-slate-900">{summary.new_signups_7d}</dd>
                </div>
                <div className="rounded-xl bg-slate-50 p-4">
                    <dt className="text-xs text-slate-500">최근 7일 로드맵 생성</dt>
                    <dd className="mt-1 text-lg font-bold text-slate-900">{summary.roadmaps_generated_7d}</dd>
                </div>
            </dl>
            <p className="mt-4 text-xs text-slate-500">생성 시각: {summary.generated_at}</p>
        </section>
    );
}
