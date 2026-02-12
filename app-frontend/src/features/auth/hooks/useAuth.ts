
import { useState } from 'react';

export const useAuth = () => {
    const login = async (username: string, password: string) => {
        // Use API client to call login endpoint
        // Endpoint expects form-data encoding for OAuth2PasswordRequestForm
        // But our api-client sends JSON by default.
        // We need to adjust either api-client or make specific call here.
        // FastAPI OAuth2PasswordRequestForm expects form-data.

        const params = new URLSearchParams();
        params.append('username', username);
        params.append('password', password);

        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: params,
        });

        if (!response.ok) {
            throw new Error('Login failed');
        }

        const data = await response.json();
        // Save token (localStorage for MVP)
        localStorage.setItem('token', data.access_token);
        return data;
    };

    return { login };
};
