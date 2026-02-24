"use client";

import React, { useState } from "react";
import { AlertTriangle, ShieldCheck, UserX, UserCheck, Users } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import type { OpsUser } from "../types";

interface DisciplineModalProps {
    user: OpsUser | null;
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (status: string, reason: string, duration_days?: number) => Promise<void>;
    isBulk?: boolean;
    selectedCount?: number;
}

export function DisciplineModal({ user, isOpen, onClose, onConfirm, isBulk, selectedCount }: DisciplineModalProps) {
    const [status, setStatus] = useState("suspended");
    const [reason, setReason] = useState("");
    const [durationDays, setDurationDays] = useState(7);
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!user && !isBulk) return null;

    const handleConfirm = async () => {
        if (!reason.trim()) {
            alert("처리 사유를 입력해 주세요.");
            return;
        }
        setIsSubmitting(true);
        try {
            await onConfirm(status, reason, status === "suspended" ? durationDays : undefined);
            onClose();
            setReason(""); // Reset reason
        } catch (err) {
            console.error(err);
            alert("처리에 실패했습니다.");
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        {isBulk ? <Users className="text-blue-600" size={20} /> : <ShieldCheck className="text-blue-600" size={20} />}
                        {isBulk ? `일괄 계정 관리 (${selectedCount}명)` : `계정 관리: ${user?.full_name || user?.email}`}
                    </DialogTitle>
                    <DialogDescription>
                        {isBulk ? "선택한 모든 사용자의 상태를 한꺼번에 변경합니다." : "사용자의 서비스 이용 권한 및 상태를 변경합니다."}
                    </DialogDescription>
                </DialogHeader>

                <div className="grid gap-4 py-4">
                    <div className="space-y-2">
                        <label className="text-sm font-bold text-slate-700">변경할 상태</label>
                        <div className="grid grid-cols-1 gap-2">
                            <button
                                onClick={() => setStatus("active")}
                                className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${status === "active" ? "border-blue-600 bg-blue-50 ring-1 ring-blue-600" : "border-slate-200 hover:bg-slate-50"
                                    }`}
                            >
                                <div className={`rounded-full p-2 ${status === "active" ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-400"}`}>
                                    <UserCheck size={18} />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-slate-900">정상 (Active)</p>
                                    <p className="text-xs text-slate-500">계정의 정지 상태를 해제합니다.</p>
                                </div>
                            </button>

                            <button
                                onClick={() => setStatus("suspended")}
                                className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${status === "suspended" ? "border-amber-600 bg-amber-50 ring-1 ring-amber-600" : "border-slate-200 hover:bg-slate-50"
                                    }`}
                            >
                                <div className={`rounded-full p-2 ${status === "suspended" ? "bg-amber-600 text-white" : "bg-slate-100 text-slate-400"}`}>
                                    <AlertTriangle size={18} />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-slate-900">기간 정지 (Suspended)</p>
                                    <p className="text-xs text-slate-500">이용 정책 위반으로 일시 정지합니다.</p>
                                </div>
                            </button>

                            {status === "suspended" && (
                                <div className="mt-1 p-3 bg-slate-50 rounded-lg border border-dashed border-slate-300">
                                    <label className="text-[11px] font-bold text-slate-500 uppercase tracking-tight block mb-2">정지 기간 선택</label>
                                    <div className="flex flex-wrap gap-2">
                                        {[1, 3, 7, 14, 30].map((d) => (
                                            <button
                                                key={d}
                                                type="button"
                                                onClick={() => setDurationDays(d)}
                                                className={`px-3 py-1.5 rounded-md text-xs font-bold transition-all ${durationDays === d
                                                    ? "bg-amber-600 text-white shadow-sm"
                                                    : "bg-white border border-slate-200 text-slate-600 hover:border-amber-300"
                                                    }`}
                                            >
                                                {d}일
                                            </button>
                                        ))}
                                    </div>
                                    <p className="text-[10px] text-slate-400 mt-2 font-medium italic">* 선택한 기간이 지나면 로그인 시 자동으로 정상 복구됩니다.</p>
                                </div>
                            )}

                            <button
                                onClick={() => setStatus("suspended_permanent")}
                                className={`flex items-center gap-3 rounded-lg border p-3 text-left transition-all ${status === "suspended_permanent" ? "border-red-600 bg-red-50 ring-1 ring-red-600" : "border-slate-200 hover:bg-slate-50"
                                    }`}
                            >
                                <div className={`rounded-full p-2 ${status === "suspended_permanent" ? "bg-red-600 text-white" : "bg-slate-100 text-slate-400"}`}>
                                    <UserX size={18} />
                                </div>
                                <div>
                                    <p className="text-sm font-bold text-slate-900">영구 차단 (Banned)</p>
                                    <p className="text-xs text-slate-500">계정을 영구적으로 차단합니다.</p>
                                </div>
                            </button>
                        </div>
                    </div>

                    <div className="space-y-2">
                        <label className="text-sm font-bold text-slate-700">처리 사유 <span className="text-red-500">*</span></label>
                        <textarea
                            value={reason}
                            onChange={(e) => setReason(e.target.value)}
                            placeholder="상태 변경 사유를 상세히 입력해 주세요 (감사로그에 기록됩니다)."
                            className="w-full min-h-[100px] rounded-lg border border-slate-200 p-3 text-sm focus:border-blue-500 focus:ring-4 focus:ring-blue-50 outline-none resize-none"
                        />
                    </div>
                </div>

                <DialogFooter>
                    <Button variant="ghost" onClick={onClose} disabled={isSubmitting}>
                        취소
                    </Button>
                    <Button
                        onClick={handleConfirm}
                        disabled={isSubmitting}
                        className={status === "active" ? "bg-blue-600 hover:bg-blue-700" : status === "suspended" ? "bg-amber-600 hover:bg-amber-700" : "bg-red-600 hover:bg-red-700"}
                    >
                        {isSubmitting ? "처리 중..." : "변경 사항 적용"}
                    </Button>
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}
