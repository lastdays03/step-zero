import React from 'react';
import { ShieldAlert, AlertTriangle, AlertCircle, CalendarClock } from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";
import { Button } from '@/components/ui/button';

export interface SuspensionModalProps {
    isOpen: boolean;
    onClose: () => void;
    reason: string;
    expiry: string | null;
    expiryIso?: string | null;
}

export const SuspensionModal: React.FC<SuspensionModalProps> = ({ isOpen, onClose, reason, expiry, expiryIso }) => {
    const [timeRemaining, setTimeRemaining] = React.useState<string | null>(null);

    React.useEffect(() => {
        if (!isOpen || !expiryIso) {
            setTimeRemaining(null);
            return;
        }

        const updateRemainingTime = () => {
            const now = new Date();
            const end = new Date(expiryIso);
            const diff = end.getTime() - now.getTime();

            if (diff <= 0) {
                setTimeRemaining("정지 해제됨 (새로고침 요망)");
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));

            let remainingString = "";
            if (days > 0) remainingString += `${days}일 `;
            if (hours > 0) remainingString += `${hours}시간 `;
            remainingString += `${minutes}분 남음`;

            setTimeRemaining(remainingString);
        };

        updateRemainingTime();
        const interval = setInterval(updateRemainingTime, 60000); // 1분마다 업데이트

        return () => clearInterval(interval);
    }, [isOpen, expiryIso]);

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-md bg-white border-0 shadow-2xl rounded-2xl p-0 overflow-hidden">
                {/* Red Header Bar */}
                <div className="bg-red-500 p-6 flex flex-col items-center justify-center text-white relative">
                    <div className="absolute inset-0 overflow-hidden opacity-20 bg-[url('https://www.transparenttextures.com/patterns/diagonal-striped-brick.png')]"></div>
                    <div className="w-16 h-16 rounded-full bg-white/20 flex items-center justify-center mb-4 z-10 backdrop-blur-sm shadow-inner ring-4 ring-red-400">
                        <ShieldAlert size={36} className="text-white drop-shadow-md animate-pulse" />
                    </div>
                    <DialogTitle className="text-2xl font-bold tracking-tight z-10 text-center">
                        접근 제한 안내
                    </DialogTitle>
                    <p className="text-red-100 mt-2 font-medium z-10 text-center text-sm">
                        해당 계정은 운영 정책 위반으로 서비스 이용이 제한되었습니다.
                    </p>
                </div>

                {/* Content Area */}
                <div className="p-6 space-y-6 bg-slate-50">
                    <div className="bg-white rounded-xl border border-red-100 shadow-sm overflow-hidden">
                        <div className="bg-red-50 px-4 py-3 border-b border-red-100 flex items-center gap-2">
                            <AlertCircle size={16} className="text-red-600" />
                            <h3 className="text-sm font-bold text-red-900">제한 사유</h3>
                        </div>
                        <div className="p-4 text-sm text-slate-700 font-medium leading-relaxed min-h-[60px] flex items-center">
                            {reason || "운영 정책 위반"}
                        </div>
                    </div>

                    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                        <div className="bg-slate-100 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <CalendarClock size={16} className="text-slate-600" />
                                <h3 className="text-sm font-bold text-slate-800">제한 기간</h3>
                            </div>
                            {timeRemaining && (
                                <span className="text-xs font-bold text-red-600 bg-red-50 px-2 py-0.5 rounded-md animate-pulse">
                                    {timeRemaining}
                                </span>
                            )}
                        </div>
                        <div className="p-4 text-sm font-bold text-slate-900 flex items-center justify-between">
                            <span>해제 예정일시</span>
                            <span className="text-blue-600 bg-blue-50 px-3 py-1 rounded-full">{expiry || "영구 정지"}</span>
                        </div>
                    </div>

                    <div className="flex gap-3 pt-2">
                        <Button
                            onClick={onClose}
                            className="w-full h-12 text-base font-bold bg-slate-800 hover:bg-slate-900 text-white rounded-xl shadow-lg shadow-slate-200 transition-all active:scale-[0.98]"
                        >
                            확인
                        </Button>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
};
