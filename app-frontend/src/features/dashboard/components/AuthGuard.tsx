"use client";

import { useCallback, useEffect, useState } from "react";
import { SocialAuthModal } from "@/features/auth/components/SocialAuthModal";
import { AUTH_STORAGE_EVENT } from "@/lib/api-client";

// Module-level flag — survives re-renders, no lint issues
let hadToken = typeof window !== "undefined" && !!localStorage.getItem("token");

/**
 * Session expiry banner — shown inside the dashboard when a
 * previously-logged-in user's session expires.  Does NOT block
 * guest access; guests can browse freely.
 *
 * All setState calls happen inside event listener callbacks
 * (async context), avoiding react-hooks/set-state-in-effect.
 */
export function SessionExpiredBanner() {
    const [expired, setExpired] = useState(false);
    const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

    useEffect(() => {
        const handleAuthChange = () => {
            const hasToken = !!localStorage.getItem("token");
            if (hasToken) {
                hadToken = true;
                setExpired(false);
            } else if (hadToken) {
                hadToken = false;
                setExpired(true);
            }
        };

        window.addEventListener(AUTH_STORAGE_EVENT, handleAuthChange);
        return () => window.removeEventListener(AUTH_STORAGE_EVENT, handleAuthChange);
    }, []);

    const handleDismiss = useCallback(() => setExpired(false), []);

    if (!expired) return null;

    return (
        <>
            <div className="mb-4 flex items-center justify-between rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800 shadow-sm">
                <span>세션이 만료되었습니다. 다시 로그인해주세요.</span>
                <div className="flex items-center gap-2">
                    <button
                        type="button"
                        onClick={() => setIsAuthModalOpen(true)}
                        className="rounded-lg bg-amber-600 px-3 py-1 text-xs font-bold text-white hover:bg-amber-700 transition-colors"
                    >
                        로그인
                    </button>
                    <button
                        type="button"
                        onClick={handleDismiss}
                        className="text-amber-400 hover:text-amber-600"
                    >
                        ✕
                    </button>
                </div>
            </div>
            <SocialAuthModal
                isOpen={isAuthModalOpen}
                onClose={() => setIsAuthModalOpen(false)}
            />
        </>
    );
}
