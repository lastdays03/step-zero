"use client";

import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Sparkles } from 'lucide-react';
import { GoogleLogin } from '@react-oauth/google';

import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/providers/AuthProvider';
import { SuspensionModal } from './SuspensionModal';

interface SocialAuthModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const SocialAuthModal = ({ isOpen, onClose }: SocialAuthModalProps) => {
    const { login } = useAuth();
    const [isSuspended, setIsSuspended] = React.useState(false);
    const [suspensionReason, setSuspensionReason] = React.useState('');
    const [suspensionExpiry, setSuspensionExpiry] = React.useState<string | null>(null);
    const [suspensionExpiryIso, setSuspensionExpiryIso] = React.useState<string | null>(null);

    const completeLogin = (payload: {
        access_token: string;
        refresh_token?: string;
        user: { id: number | string; full_name?: string | null; email: string; is_superuser?: boolean | null };
        current_team_id?: string;
    }) => {
        const { access_token, refresh_token, user, current_team_id } = payload;
        const fullName = typeof user.full_name === 'string' ? user.full_name : undefined;
        const userData = {
            id: user.id.toString(),
            username: fullName || user.email.split('@')[0],
            email: user.email,
            full_name: fullName,
            is_superuser: Boolean(user.is_superuser),
        };

        login(access_token, userData, current_team_id, refresh_token);
        onClose();
        window.location.reload();
    };

    const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
        if (!credentialResponse.credential) {
            alert('구글 로그인 토큰을 받지 못했습니다.');
            return;
        }
        try {
            const response = await apiClient.post('/auth/login/google', {
                id_token: credentialResponse.credential,
            });
            completeLogin(response.data);
        } catch (error: unknown) {
            const status = (error as { response?: { status?: number } })?.response?.status;
            const detail = (error as { response?: { data?: { detail?: string } } })?.response?.data?.detail;

            console.error('Google login verification failed:', error);
            if (status === 401) {
                alert('구글 로그인 토큰 검증에 실패했습니다. Google Client ID 설정과 토큰 발급 계정을 확인해주세요.');
                return;
            }
            if (status === 503) {
                if (detail === 'Authentication backend unavailable') {
                    alert('로그인 서버가 데이터베이스에 연결되지 않았습니다. 백엔드/DB 상태를 먼저 확인해주세요.');
                    return;
                }
                try {
                    const fallback = await apiClient.post('/auth/login/social/google');
                    completeLogin(fallback.data);
                    return;
                } catch (fallbackError: any) {
                    if (fallbackError?.response?.status === 403) {
                        const fallbackDetail = fallbackError.response.data?.detail || {};
                        setSuspensionReason(fallbackDetail.reason || '운영 정책 위반');
                        setSuspensionExpiry(fallbackDetail.expiry || '영구 정지');
                        setSuspensionExpiryIso(fallbackDetail.expiry_iso || null);
                        setIsSuspended(true);
                        return;
                    }

                    const fallbackDetailStr = fallbackError?.response?.data?.detail;
                    alert(
                        fallbackDetailStr
                        || '구글 인증 서비스 연결에 실패했습니다. 잠시 후 다시 시도하거나 일반 로그인으로 진행해주세요.',
                    );
                    return;
                }
            }

            if (status === 403) {
                const detailObj = (error as any)?.response?.data?.detail || {};
                setSuspensionReason(detailObj.reason || '운영 정책 위반');
                setSuspensionExpiry(detailObj.expiry || '영구 정지');
                setSuspensionExpiryIso(detailObj.expiry_iso || null);
                setIsSuspended(true);
                return;
            }

            alert(detail || '구글 로그인 검증에 실패했습니다.');
        }
    };

    return (
        <>
            <Dialog open={isOpen && !isSuspended} onOpenChange={onClose}>
                <DialogContent className="sm:max-w-md bg-white/90 backdrop-blur-xl border-white/50 shadow-2xl rounded-2xl p-8">
                    <DialogHeader className="flex flex-col items-center text-center space-y-4">
                        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-[#36a4f2] to-purple-400 flex items-center justify-center shadow-lg transform rotate-3 hover:rotate-0 transition-transform duration-300">
                            <Sparkles className="w-8 h-8 text-white" />
                        </div>
                        <div className="space-y-2">
                            <DialogTitle className="text-2xl font-bold text-slate-900">
                                창업의 시작, StepZero
                            </DialogTitle>
                            <DialogDescription className="text-slate-500 font-medium">
                                3초 만에 시작하고 나만의 로드맵을 평생 소장하세요.
                            </DialogDescription>
                        </div>
                    </DialogHeader>

                    <div className="flex flex-col gap-3 mt-6">
                        <div className="w-full flex justify-center py-2">
                            <GoogleLogin
                                onSuccess={handleGoogleSuccess}
                                onError={() => {
                                    console.error('Google Login Failed');
                                    alert('구글 로그인에 실패했습니다.');
                                }}
                                text="signin_with"
                                shape="pill"
                                size="large"
                                width="320"
                            />
                        </div>
                    </div>

                    <div className="mt-8 pt-6 border-t border-slate-100 flex flex-col items-center gap-2">
                        <p className="text-[10px] text-slate-400 text-center">
                            계속 진행함으로써 StepZero의 <span className="underline cursor-pointer">이용약관</span> 및 <span className="underline cursor-pointer">개인정보처리방침</span>에 동의하게 됩니다.
                        </p>
                    </div>
                </DialogContent>
            </Dialog>

            <SuspensionModal
                isOpen={isSuspended}
                onClose={() => {
                    setIsSuspended(false);
                    onClose();
                }}
                reason={suspensionReason}
                expiry={suspensionExpiry}
                expiryIso={suspensionExpiryIso}
            />
        </>
    );
};
