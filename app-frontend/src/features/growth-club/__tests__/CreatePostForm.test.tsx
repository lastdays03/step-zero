import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CreatePostForm } from '../components/CreatePostForm';

// ---- Mocks ----

jest.mock('next/image', () => ({
  __esModule: true,
  default: (props: Record<string, unknown>) => {
    const { fill, unoptimized, ...rest } = props;
    void fill; void unoptimized;
    // eslint-disable-next-line @next/next/no-img-element, jsx-a11y/alt-text
    return <img {...rest} />;
  },
}));

jest.mock('sonner', () => ({
  toast: { error: jest.fn(), warning: jest.fn() },
}));

jest.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 1 } }),
}));

jest.mock('../api', () => ({
  growthClubApi: {
    createPost: jest.fn(),
  },
}));

import { growthClubApi } from '../api';

const mockCreatePost = growthClubApi.createPost as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('CreatePostForm', () => {
  const mockOnSuccess = jest.fn();

  it('폼 필드 렌더링 (제목, 내용, 카테고리, 등록 버튼)', () => {
    render(<CreatePostForm onSuccess={mockOnSuccess} />);

    expect(screen.getByPlaceholderText('제목을 입력하세요')).toBeDefined();
    expect(screen.getByPlaceholderText(/오늘 어떤 일이/)).toBeDefined();
    expect(screen.getByText('자유게시판')).toBeDefined();
    expect(screen.getByText('동네 소식')).toBeDefined();
    expect(screen.getByText('업종 이야기')).toBeDefined();
    expect(screen.getByText('등록하기')).toBeDefined();
  });

  it('카테고리 선택 변경', () => {
    render(<CreatePostForm onSuccess={mockOnSuccess} />);

    const neighborBtn = screen.getByText('동네 소식');
    fireEvent.click(neighborBtn);

    // 동네 소식 버튼이 활성 스타일 (bg-blue-600) 적용
    expect(neighborBtn.className).toContain('bg-blue-600');
  });

  it('제목/내용 없으면 제출 버튼 disabled', () => {
    render(<CreatePostForm onSuccess={mockOnSuccess} />);

    const submitBtn = screen.getByText('등록하기').closest('button')!;
    expect(submitBtn).toBeDisabled();
  });

  it('폼 제출 시 createPost 호출 + onSuccess 콜백', async () => {
    mockCreatePost.mockResolvedValue({});

    render(<CreatePostForm onSuccess={mockOnSuccess} />);

    fireEvent.change(screen.getByPlaceholderText('제목을 입력하세요'), {
      target: { value: '테스트 제목' },
    });
    fireEvent.change(screen.getByPlaceholderText(/오늘 어떤 일이/), {
      target: { value: '테스트 내용입니다' },
    });

    const submitBtn = screen.getByText('등록하기').closest('button')!;
    expect(submitBtn).not.toBeDisabled();

    fireEvent.click(submitBtn);

    await waitFor(() => {
      expect(mockCreatePost).toHaveBeenCalled();
    });

    await waitFor(() => {
      expect(mockOnSuccess).toHaveBeenCalled();
    });
  });

  it('이미지/파일 추가 버튼 존재', () => {
    render(<CreatePostForm onSuccess={mockOnSuccess} />);

    expect(screen.getByTitle('이미지 추가')).toBeDefined();
    expect(screen.getByTitle('파일 추가')).toBeDefined();
  });
});
