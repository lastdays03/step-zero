
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import { LoginForm } from '../components/LoginForm';
import { useAuth } from '../hooks/useAuth';

// Mock the useAuth hook
jest.mock('../hooks/useAuth', () => ({
    useAuth: jest.fn(),
}));

const mockPush = jest.fn();
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: mockPush,
    }),
}));

describe('LoginForm', () => {
    const mockLoginWithCredentials = jest.fn();

    beforeEach(() => {
        jest.mocked(useAuth).mockReturnValue({
            login: mockLoginWithCredentials,
            loginWithCredentials: mockLoginWithCredentials,
        });
        mockLoginWithCredentials.mockClear();
        mockPush.mockClear();
    });

    it('renders login form correctly', () => {
        render(<LoginForm />);
        expect(screen.getByPlaceholderText(/email/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /로그인/i })).toBeInTheDocument();
    });

    it('calls loginWithCredentials on form submission', async () => {
        mockLoginWithCredentials.mockResolvedValue(undefined);
        render(<LoginForm />);

        const emailInput = screen.getByPlaceholderText(/email/i);
        const passwordInput = screen.getByPlaceholderText(/password/i);
        const submitButton = screen.getByRole('button', { name: /로그인/i });

        fireEvent.change(emailInput, { target: { value: 'test@example.com' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });

        fireEvent.click(submitButton);

        expect(mockLoginWithCredentials).toHaveBeenCalledWith('test@example.com', 'password123');
    });
});
