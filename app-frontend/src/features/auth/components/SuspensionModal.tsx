"use client";

import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { ShieldAlert, Calendar, Info, Mail } from 'lucide-react';

interface SuspensionModalProps {
    isOpen: boolean;
    onClose: () => void;
    suspensionInfo: {
        reason: string;
        suspended_until: string;
        status: string;
    } | null;
}

export const SuspensionModal = ({ isOpen, onClose, suspensionInfo }: SuspensionModalProps) => {
    if (!suspensionInfo) return null;

    const isBanned = suspensionInfo.status === 'banned' || suspensionInfo.suspended_until === '영구';

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md bg-white/95 backdrop-blur-2xl border-white/50 shadow-2xl rounded-3xl p-0 overflow-hidden">
                <div className="absolute top-0 inset-x-0 h-1.5 bg-gradient-to-r from-red-500 via-orange-500 to-red-500" />

                <div className="p-8">
                    <DialogHeader className="flex flex-col items-center text-center space-y-6">
                        <div className="w-20 h-20 rounded-3xl bg-red-50 flex items-center justify-center relative group">
                            <div className="absolute inset-0 bg-red-100/50 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300 opacity-0 group-hover:opacity-100" />
                            <ShieldAlert className="w-10 h-10 text-red-500 relative z-10" />
                        </div>

                        <div className="space-y-2">
                            <DialogTitle className="text-2xl font-extrabold text-zinc-900 tracking-tight">
                                {isBanned ? "계정 이용이 영구 차단되었습니다" : "계정 이용이 일시 정지되었습니다"}
                            </DialogTitle>
                            <DialogDescription className="text-zinc-500 font-medium">
                                운영 정책 위반으로 인해 서비스 접근이 제한되었습니다.
                            </DialogDescription>
                        </div>
                    </DialogHeader>

                    <div className="mt-8 space-y-4">
                        {/* Reason Box */}
                        <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-5 space-y-2">
                            <div className="flex items-center gap-2 text-zinc-400">
                                <Info size={14} />
                                <span className="text-[10px] font-bold uppercase tracking-wider">제한 사유</span>
                            </div>
                            <p className="text-sm text-zinc-700 leading-relaxed font-medium">
                                {suspensionInfo.reason}
                            </p>
                        </div>

                        {/* Duration Box */}
                        {!isBanned && (
                            <div className="bg-zinc-50 border border-zinc-100 rounded-2xl p-5 space-y-2">
                                <div className="flex items-center gap-2 text-zinc-400">
                                    <Calendar size={14} />
                                    <span className="text-[10px] font-bold uppercase tracking-wider">제한 종료일</span>
                                </div>
                                <p className="text-sm text-red-600 font-bold">
                                    {suspensionInfo.suspended_until} 23:59까지
                                </p>
                            </div>
                        )}
                    </div>

                    <div className="mt-8 space-y-3">
                        <button
                            onClick={onClose}
                            className="w-full py-4 bg-zinc-900 text-white rounded-2xl font-bold hover:bg-zinc-800 transition-all active:scale-[0.98] shadow-lg shadow-zinc-200"
                        >
                            확인
                        </button>

                        <a
                            href="mailto:support@stepzero.com"
                            className="flex items-center justify-center gap-2 text-xs text-zinc-400 hover:text-zinc-600 transition-colors py-2"
                        >
                            <Mail size={12} />
                            문의하기: support@stepzero.com
                        </a>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};
