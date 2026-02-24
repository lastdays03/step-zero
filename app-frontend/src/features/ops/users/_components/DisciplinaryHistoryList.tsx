"use client";

import { useEffect, useState } from "react";
import { Loader2, AlertCircle } from "lucide-react";
import { fetchUserHistory } from "../api";
import type { DisciplineHistory } from "../types";

interface DisciplinaryHistoryListProps {
    userId: number;
}

export function DisciplinaryHistoryList({ userId }: DisciplinaryHistoryListProps) {
    const [histories, setHistories] = useState<DisciplineHistory[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const load = async () => {
            try {
                const data = await fetchUserHistory(userId);
                setHistories(data);
            } catch {
                setError("기록을 불러오는 데 실패했습니다.");
            } finally {
                setIsLoading(false);
            }
        };
        void load();
    }, [userId]);

    const toKST = (dateStr: string) => {
        const utcStr = dateStr.includes('Z') || dateStr.includes('+') ? dateStr : `${dateStr.replace(' ', 'T')}Z`;
        return new Date(utcStr).toLocaleString("ko-KR", {
            timeZone: "Asia/Seoul",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            hour12: false,
        });
    };

    if (isLoading) return <div className="p-4 text-center"><Loader2 className="animate-spin mx-auto h-5 w-5 text-slate-400" /></div>;
    if (error) return <div className="p-4 text-sm text-red-500 flex items-center gap-2"><AlertCircle size={16} /> {error}</div>;
    if (histories.length === 0) return <div className="p-4 text-sm text-slate-400 text-center italic">정지 기록이 없습니다.</div>;

    return (
        <div className="bg-slate-50/50 rounded-lg border border-slate-100 divide-y divide-slate-100 max-h-[300px] overflow-y-auto">
            {histories.map((h) => (
                <div key={h.id} className="p-3 text-xs">
                    <div className="flex justify-between items-start mb-1">
                        <div className="font-bold text-slate-700">
                            {h.prev_status} → <span className="text-blue-600">{h.new_status}</span>
                        </div>
                        <div className="text-slate-400">{toKST(h.created_at)}</div>
                    </div>
                    <p className="text-slate-600 line-clamp-2">{h.reason}</p>
                </div>
            ))}
        </div>
    );
}
