"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { apiClient } from '@/lib/api-client';

interface User {
    id: string;
    username: string;
    email: string;
    full_name?: string;
}

interface LoginResponse {
    access_token: string;
    token_type: string;
    user?: {
        id: number | string;
        email: string;
        full_name?: string | null;
    };
}

interface AuthContextType {
    user: User | null;
    isLoggedIn: boolean;
    login: (token: string, userData: User) => void;
    loginWithCredentials: (email: string, password: string) => Promise<void>;
    logout: () => void;
    isGuest: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [isLoggedIn, setIsLoggedIn] = useState(false);

    useEffect(() => {
        // Load auth from local storage on mount
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        if (storedToken && storedUser) {
            try {
                setUser(JSON.parse(storedUser));
                setIsLoggedIn(true);
            } catch (e) {
                console.error("Failed to parse user data", e);
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
        }
    }, []);

    const login = (token: string, userData: User) => {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(userData));
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

        const data = response.data as LoginResponse;
        const accessToken = data?.access_token;
        if (!accessToken) {
            throw new Error('Login token is missing in response');
        }

        const userData: User = data.user
            ? {
                id: String(data.user.id),
                username: data.user.full_name || data.user.email.split('@')[0] || data.user.email,
                email: data.user.email,
                full_name: data.user.full_name || undefined,
            }
            : {
                id: email,
                username: email.split('@')[0] || email,
                email,
            };
        login(accessToken, userData);
    };

    const logout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
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
