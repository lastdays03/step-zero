
"use client";

import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { SuspensionModal } from './SuspensionModal';

export const LoginForm = () => {
    const { loginWithCredentials } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [suspensionInfo, setSuspensionInfo] = useState<{ reason: string; suspended_until: string; status: string } | null>(null);
    const [isSuspensionOpen, setIsSuspensionOpen] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        try {
            await loginWithCredentials(email, password);
        } catch (err: unknown) {
            console.error('Login error:', err);

            // Axios error response check
            const axiosErr = err as { response?: { status?: number; data?: Record<string, string> } };
            const status = axiosErr?.response?.status;
            const data = axiosErr?.response?.data;

            if (status === 403 && data?.error_code === 'ACCOUNT_RESTRICTED') {
                const ext = (data as Record<string, unknown>)?.extensions as Record<string, string> | undefined;
                setSuspensionInfo({
                    reason: ext?.reason || '운영 정책 위반으로 계정이 제한되었습니다.',
                    suspended_until: ext?.suspended_until || '영구',
                    status: ext?.status || 'suspended'
                });
                setIsSuspensionOpen(true);
                return;
            }

            const message = typeof data?.detail === 'string'
                ? data.detail
                : (data?.message || '로그인에 실패했습니다. 이메일과 비밀번호를 확인해주세요.');
            setError(message);
        }
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <input
                    type="email"
                    placeholder="Email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full p-2 border rounded"
                />
            </div>
            <div>
                <input
                    type="password"
                    placeholder="Password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full p-2 border rounded"
                />
            </div>
            {error && <div className="text-red-500">{error}</div>}
            <button
                type="submit"
                className="w-full p-2 bg-zinc-900 text-white rounded font-bold hover:bg-zinc-800 transition-colors"
            >
                로그인
            </button>

            <SuspensionModal
                isOpen={isSuspensionOpen}
                onClose={() => setIsSuspensionOpen(false)}
                suspensionInfo={suspensionInfo}
            />
        </form>
    );
};
