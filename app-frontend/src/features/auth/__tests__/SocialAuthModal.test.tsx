import React from 'react';
import { render, screen } from '@testing-library/react';

import { SocialAuthModal } from '../components/SocialAuthModal';

jest.mock('sonner', () => ({
  toast: {
    error: jest.fn(),
  },
}));

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    post: jest.fn(),
  },
}));

jest.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({
    login: jest.fn(),
  }),
}));

jest.mock('../components/SuspensionModal', () => ({
  SuspensionModal: () => null,
}));

jest.mock('@react-oauth/google', () => ({
  GoogleLogin: () => <div data-testid="google-login">Google Login</div>,
}));

describe('SocialAuthModal', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  it('NEXT_PUBLIC_GOOGLE_CLIENT_ID가 없으면 fallback 안내를 표시한다', () => {
    delete process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

    render(<SocialAuthModal isOpen onClose={jest.fn()} />);

    expect(
      screen.getByText('Google 로그인이 현재 비활성화되어 있습니다.'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: '이메일 로그인 페이지로 이동' }),
    ).toHaveAttribute('href', '/login');
    expect(screen.queryByTestId('google-login')).not.toBeInTheDocument();
  });

  it('NEXT_PUBLIC_GOOGLE_CLIENT_ID가 있으면 GoogleLogin을 렌더링한다', () => {
    process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID = 'test-google-client-id';

    render(<SocialAuthModal isOpen onClose={jest.fn()} />);

    expect(screen.getByTestId('google-login')).toBeInTheDocument();
    expect(
      screen.queryByText('Google 로그인이 현재 비활성화되어 있습니다.'),
    ).not.toBeInTheDocument();
  });
});
