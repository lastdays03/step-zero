"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/providers/AuthProvider";
import { apiClient } from "@/lib/api-client";

type OpsUser = {
    id: number;
    email: string;
    full_name: string | null;
    is_active: boolean;
    is_superuser: boolean;
    created_at: string;
};

export default function OpsUsersPage() {
    const router = useRouter();
    const { isLoggedIn, canAccessOps } = useAuth();
    const [users, setUsers] = useState<OpsUser[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!isLoggedIn) {
            router.replace("/login");
            return;
        }
        if (!canAccessOps) {
            router.replace("/dashboard");
            return;
        }

        const load = async () => {
            try {
                const response = await apiClient.get("/ops/users");
                setUsers(response.data as OpsUser[]);
            } catch (err) {
                setError(err instanceof Error ? err.message : "알 수 없는 오류가 발생했습니다.");
            } finally {
                setIsLoading(false);
            }
        };

        void load();
    }, [canAccessOps, isLoggedIn, router]);

    if (isLoading) {
        return <p className="text-sm text-slate-600">사용자 목록을 불러오는 중입니다...</p>;
    }
    if (error) {
        return <p className="text-sm text-red-600">{error}</p>;
    }
    if (!users.length) {
        return <p className="text-sm text-slate-600">조회된 사용자가 없습니다.</p>;
    }

    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-6">
            <h1 className="text-xl font-bold text-slate-900">플랫폼 사용자</h1>
            <ul className="mt-4 divide-y divide-slate-100">
                {users.map((user) => (
                    <li key={user.id} className="py-3">
                        <p className="text-sm font-semibold text-slate-900">{user.email}</p>
                        <p className="text-xs text-slate-500">
                            {user.full_name || "이름 없음"} | {user.is_active ? "활성" : "비활성"} |{" "}
                            {user.is_superuser ? "운영자" : "일반"}
                        </p>
                    </li>
                ))}
            </ul>
        </section>
    );
}
