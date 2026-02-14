"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';
import type { TokenWithTeams } from '@/lib/api-types';

interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
}

interface AuthContextType {
    user: User | null;
    isLoggedIn: boolean;
    login: (token: string, userData: User, currentTeamId?: string) => void;
    loginWithCredentials: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isGuest: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const asOptionalString = (value: unknown): string | undefined =>
    typeof value === 'string' && value.trim() ? value : undefined;

const getInitialAuthState = (): { user: User | null; isLoggedIn: boolean } => {
    if (typeof window === 'undefined') {
        return { user: null, isLoggedIn: false };
    }

    const storedToken = localStorage.getItem('token');
    const storedUser = localStorage.getItem('user');
    if (!storedToken || !storedUser) {
        return { user: null, isLoggedIn: false };
    }

    try {
        return { user: JSON.parse(storedUser) as User, isLoggedIn: true };
    } catch (e) {
        console.error("Failed to parse user data", e);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('current_team_id');
        return { user: null, isLoggedIn: false };
    }
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const initialAuthState = getInitialAuthState();
    const [user, setUser] = useState<User | null>(initialAuthState.user);
    const [isLoggedIn, setIsLoggedIn] = useState(initialAuthState.isLoggedIn);

    const login = (token: string, userData: User, currentTeamId?: string) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
        if (currentTeamId) {
            localStorage.setItem('current_team_id', currentTeamId);
        }
        setUser(userData);
        setIsLoggedIn(true);
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
        setUser(null);
        setIsLoggedIn(false);
    };

    return (
        <AuthContext.Provider value={{
            user,
            isLoggedIn,
            login,
            loginWithCredentials,
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
