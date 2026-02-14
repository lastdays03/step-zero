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

interface SocialAuthModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const SocialAuthModal = ({ isOpen, onClose }: SocialAuthModalProps) => {
    const { login } = useAuth();

    const handleGoogleSuccess = async (credentialResponse: { credential?: string }) => {
        if (!credentialResponse.credential) {
            alert('구글 로그인 토큰을 받지 못했습니다.');
            return;
        }
        try {
            const response = await apiClient.post('/auth/login/google', {
                id_token: credentialResponse.credential,
            });

            const { access_token, user, current_team_id } = response.data;
            const userData = {
                id: user.id.toString(),
                username: user.full_name || user.email.split('@')[0],
                email: user.email,
                full_name: user.full_name,
            };

            login(access_token, userData, current_team_id);
            onClose();
            window.location.reload();
        } catch (error) {
            console.error('Google login verification failed:', error);
            alert('구글 로그인 검증에 실패했습니다.');
        }
    };

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
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
    );
};
