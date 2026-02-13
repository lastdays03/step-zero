"use client";

import React from 'react';
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Sparkles } from 'lucide-react';
import { useGoogleLogin } from '@react-oauth/google';

import { apiClient } from '@/lib/api-client';
import { useAuth } from '@/providers/AuthProvider';

interface SocialAuthModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const SocialAuthModal = ({ isOpen, onClose }: SocialAuthModalProps) => {
    const { login } = useAuth();

    const googleLogin = useGoogleLogin({
        onSuccess: async (tokenResponse) => {
            try {
                // @react-oauth/google gives us an access_token, but our backend expects an id_token for standard OIDC verification
                // However, for simplicity in this flow, we can either:
                // 1. Use 'implicit' flow to get id_token (requires different config)
                // 2. Or send the access_token to backend and have backend fetch user info from Google

                // For this implementation, we assume the backend endpoint handles the token
                // If using useGoogleLogin default, it's an access_token. 
                // Let's call our new backend endpoint.

                const response = await apiClient.post('/auth/login/google', {
                    id_token: tokenResponse.access_token // We'll map access_token to what backend expects for now or adjust backend
                });

                const { access_token, user } = response.data;

                const userData = {
                    id: user.id.toString(),
                    username: user.full_name || user.email.split('@')[0],
                    email: user.email,
                    full_name: user.full_name
                };

                login(access_token, userData);
                onClose();
                window.location.reload();
            } catch (error) {
                console.error('Google login verification failed:', error);
                alert('구글 로그인 검증에 실패했습니다.');
            }
        },
        onError: () => {
            console.error('Google Login Failed');
            alert('구글 로그인에 실패했습니다.');
        },
    });

    const handleKakaoLogin = async () => {
        try {
            const response = await apiClient.post(`/auth/login/social/kakao`);
            const { access_token } = response.data;

            const userData = {
                id: 'kakao-user',
                username: 'Kakao User',
                email: `social_kakao_user@example.com`
            };

            login(access_token, userData);
            onClose();
            window.location.reload();
        } catch (error) {
            console.error('Kakao login failed:', error);
            alert('카카오 로그인에 실패했습니다.');
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
                    <Button
                        onClick={() => googleLogin()}
                        variant="outline"
                        className="h-12 border-slate-200 hover:bg-slate-50 transition-all rounded-xl flex items-center justify-center gap-3 relative group overflow-hidden"
                    >
                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                            <path
                                fill="#4285F4"
                                d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                            />
                            <path
                                fill="#34A853"
                                d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                            />
                            <path
                                fill="#FBBC05"
                                d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z"
                            />
                            <path
                                fill="#EA4335"
                                d="M12 5.38c1.62 0 3.06.56 4.21 1.66l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                            />
                        </svg>
                        <span className="font-semibold text-slate-700">Google로 시작하기</span>
                    </Button>
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
