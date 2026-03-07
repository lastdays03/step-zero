"use client";

import { createContext, useCallback, useContext, useState } from "react";
import { SocialAuthModal } from "@/features/auth";

interface AuthModalContextValue {
    openAuthModal: () => void;
}

const AuthModalContext = createContext<AuthModalContextValue | null>(null);

export function useAuthModal() {
    const ctx = useContext(AuthModalContext);
    if (!ctx) throw new Error("useAuthModal must be used within AuthModalProvider");
    return ctx;
}

export function AuthModalProvider({ children }: { children: React.ReactNode }) {
    const [isOpen, setIsOpen] = useState(false);
    const openAuthModal = useCallback(() => setIsOpen(true), []);

    return (
        <AuthModalContext.Provider value={{ openAuthModal }}>
            {children}
            <SocialAuthModal isOpen={isOpen} onClose={() => setIsOpen(false)} />
        </AuthModalContext.Provider>
    );
}
