"use client";

import React, { createContext, useContext, useSyncExternalStore, ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';
import type { TokenWithTeams } from '@/lib/api-types';

interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
    is_superuser?: boolean;
}

interface AuthContextType {
    user: User | null;
    isLoggedIn: boolean;
    isAuthReady: boolean;
    canAccessOps: boolean;
    login: (token: string, userData: User, currentTeamId?: string) => void;
    loginWithCredentials: (email: string, password: string) => Promise<void>;
    updateUser: (data: Partial<User>) => void;
    logout: () => void;
    isGuest: boolean;
}

type AuthState = { user: User | null; isLoggedIn: boolean };

const AuthContext = createContext<AuthContextType | undefined>(undefined);
const AUTH_STORAGE_EVENT = 'auth-storage-changed';
const ROADMAP_JOB_STORAGE_KEY = "roadmap_polling_job_id";
const LOGGED_OUT_STATE: AuthState = { user: null, isLoggedIn: false };
let lastTokenSnapshot: string | null = null;
let lastUserSnapshot: string | null = null;
let lastAuthStateSnapshot: AuthState = LOGGED_OUT_STATE;

const asOptionalString = (value: unknown): string | undefined =>
    typeof value === 'string' && value.trim() ? value : undefined;

const getStoredAuthState = (): AuthState => {
    if (typeof window === 'undefined') {
        return LOGGED_OUT_STATE;
    }

    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (storedToken === lastTokenSnapshot && storedUser === lastUserSnapshot) {
        return lastAuthStateSnapshot;
    }

    if (!storedToken || !storedUser) {
        lastTokenSnapshot = storedToken;
        lastUserSnapshot = storedUser;
        lastAuthStateSnapshot = LOGGED_OUT_STATE;
        return LOGGED_OUT_STATE;
    }

    try {
        lastTokenSnapshot = storedToken;
        lastUserSnapshot = storedUser;
        lastAuthStateSnapshot = { user: JSON.parse(storedUser) as User, isLoggedIn: true };
        return lastAuthStateSnapshot;
    } catch (e) {
        console.error("Failed to parse user data", e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('current_team_id');
        lastTokenSnapshot = null;
        lastUserSnapshot = null;
        lastAuthStateSnapshot = LOGGED_OUT_STATE;
        return LOGGED_OUT_STATE;
    }
};

const getServerAuthState = (): AuthState => LOGGED_OUT_STATE;

const subscribeAuthState = (onStoreChange: () => void): (() => void) => {
    if (typeof window === 'undefined') {
        return () => {};
    }

    const onChange = () => onStoreChange();
    window.addEventListener('storage', onChange);
    window.addEventListener(AUTH_STORAGE_EVENT, onChange);

    return () => {
        window.removeEventListener('storage', onChange);
        window.removeEventListener(AUTH_STORAGE_EVENT, onChange);
    };
};

const notifyAuthStateChanged = () => {
    if (typeof window === 'undefined') return;
    window.dispatchEvent(new Event(AUTH_STORAGE_EVENT));
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [isAuthReady, setIsAuthReady] = React.useState(false);

    React.useEffect(() => {
        setIsAuthReady(true);
    }, []);

    const authState = useSyncExternalStore(
        subscribeAuthState,
        getStoredAuthState,
        getServerAuthState
    );
    const { user, isLoggedIn } = authState;
    const canAccessOps = Boolean(user?.is_superuser);

    const login = (token: string, userData: User, currentTeamId?: string) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        if (currentTeamId) {
            localStorage.setItem('current_team_id', currentTeamId);
        }
        notifyAuthStateChanged();
        window.location.assign('/dashboard');
    };

    const loginWithCredentials = async (email: string, password: string) => {
        const params = new URLSearchParams();
        params.append('username', email);
        params.append('password', password);

        const response = await apiClient.post('/auth/login', params, {
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
        });

        const data = response.data as TokenWithTeams;
        const accessToken = data?.access_token;
        if (!accessToken) {
            throw new Error('Login token is missing in response');
        }

        const fullName = asOptionalString(data.user?.full_name);
        const userData: User = data.user
            ? {
                id: String(data.user.id),
                username: fullName || data.user.email.split('@')[0] || data.user.email,
                email: data.user.email,
                full_name: fullName,
                is_superuser: Boolean((data.user as { is_superuser?: boolean }).is_superuser),
            }
            : {
                id: email,
                username: email.split('@')[0] || email,
                email,
            };
        login(accessToken, userData, data.current_team_id);
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('current_team_id');
        localStorage.removeItem(ROADMAP_JOB_STORAGE_KEY);
        notifyAuthStateChanged();
        window.location.assign('/dashboard');
    };

    const updateUser = (data: Partial<User>) => {
        if (!user) return;
        const updatedUser = { ...user, ...data };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        notifyAuthStateChanged();
    };

    const updateUser = (data: Partial<User>) => {
        if (!user) return;
        const updatedUser = { ...user, ...data };
        localStorage.setItem('user', JSON.stringify(updatedUser));
        notifyAuthStateChanged();
    };

    return (
        <AuthContext.Provider value={{
            user,
            isLoggedIn,
            isAuthReady,
            canAccessOps,
            login,
            loginWithCredentials,
            updateUser,
            logout,
            isGuest: !isLoggedIn
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};
