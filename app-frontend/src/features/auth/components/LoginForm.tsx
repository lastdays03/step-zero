
"use client";

import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { SuspensionModal } from './SuspensionModal';

export const LoginForm = () => {
    const { login } = useAuth();
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');

    const [isSuspended, setIsSuspended] = useState(false);
    const [suspensionReason, setSuspensionReason] = useState('');
    const [suspensionExpiry, setSuspensionExpiry] = useState<string | null>(null);
    const [suspensionExpiryIso, setSuspensionExpiryIso] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            await login(email, password);
        } catch (err: any) {
            if (err?.response?.status === 403) {
                const detail = err.response.data?.detail || {};
                setSuspensionReason(detail.reason || '운영 정책 위반');
                setSuspensionExpiry(detail.expiry || '영구 정지');
                setSuspensionExpiryIso(detail.expiry_iso || null);
                setIsSuspended(true);
                return;
            }
            if (err?.response?.status === 503) {
                setError('서비스가 현재 점검중이거나 이용 불가능합니다.');
                return;
            }
            setError('이메일 또는 비밀번호가 올바르지 않습니다.');
        }
    };

    return (
        <>
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
                    className="w-full p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
                >
                    Login
                </button>
            </form>
            <SuspensionModal
                isOpen={isSuspended}
                onClose={() => setIsSuspended(false)}
                reason={suspensionReason}
                expiry={suspensionExpiry}
                expiryIso={suspensionExpiryIso}
            />
        </>
    );
};
