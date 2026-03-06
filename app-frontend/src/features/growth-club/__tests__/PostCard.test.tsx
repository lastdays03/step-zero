import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { PostCard } from '../components/PostCard';
import { Post } from '../types';

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
  toast: { error: jest.fn(), warning: jest.fn(), info: jest.fn() },
}));

jest.mock('@/providers/AuthProvider', () => ({
  useAuth: () => ({ user: { id: 1, email: 'test@test.com', is_superuser: false } }),
}));

jest.mock('@/features/shared/file', () => ({
  resolveUploadUrl: (key: string) => `http://localhost/uploads/${key}`,
}));

jest.mock('../hooks/useTimeAgo', () => ({
  useTimeAgo: () => '1시간 전',
}));

jest.mock('../api', () => ({
  growthClubApi: {
    deletePost: jest.fn(),
    likePost: jest.fn(),
    reportPost: jest.fn(),
  },
}));

jest.mock('../components/CommentSection', () => ({
  CommentSection: () => <div data-testid="comment-section">comments</div>,
}));

import { growthClubApi } from '../api';

const mockLikePost = growthClubApi.likePost as jest.Mock;

beforeEach(() => jest.clearAllMocks());

const basePost: Post = {
  id: 1,
  title: '카페 창업 후기',
  content: '첫 달 매출이 생각보다 좋았습니다.',
  category: 'free',
  neighborhood: '강남구',
  industry: '카페',
  author: { id: 1, username: '홍길동', profile_img: 'profile.jpg' },
  created_at: '2026-01-01T00:00:00Z',
  comments: [{ id: 1, content: '축하해요', author: { id: 2, username: '김철수' }, created_at: '2026-01-01T01:00:00Z' }],
  attachments: [],
  report_count: 0,
  likes_count: 3,
  is_liked: false,
};

describe('PostCard', () => {
  it('제목, 내용, 작성자 렌더링', () => {
    render(<PostCard post={basePost} />);

    expect(screen.getByText('카페 창업 후기')).toBeDefined();
    expect(screen.getByText('첫 달 매출이 생각보다 좋았습니다.')).toBeDefined();
    expect(screen.getByText('홍길동')).toBeDefined();
  });

  it('카테고리 배지 (neighborhood, industry) 표시', () => {
    render(<PostCard post={basePost} />);

    expect(screen.getByText('강남구')).toBeDefined();
    expect(screen.getByText('카페')).toBeDefined();
  });

  it('작성자 본인이면 삭제 버튼 표시', () => {
    render(<PostCard post={basePost} />);

    expect(screen.getByTitle('게시글 삭제')).toBeDefined();
  });

  it('다른 사용자 게시글에는 삭제 버튼 없음 + 신고 버튼 표시', () => {
    const otherPost = { ...basePost, author: { id: 99, username: '다른사람' } };
    render(<PostCard post={otherPost} />);

    expect(screen.queryByTitle('게시글 삭제')).toBeNull();
    expect(screen.getByText('신고')).toBeDefined();
  });

  it('좋아요 버튼 클릭 시 낙관적 업데이트', async () => {
    mockLikePost.mockResolvedValue({ liked: true, likes_count: 4 });

    render(<PostCard post={basePost} />);

    const likeBtn = screen.getByText(/좋아요/);
    fireEvent.click(likeBtn);

    // 낙관적: 즉시 4로 변경
    expect(screen.getByText(/좋아요 4/)).toBeDefined();

    await waitFor(() => {
      expect(mockLikePost).toHaveBeenCalledWith(1);
    });
  });

  it('댓글 버튼 클릭 시 CommentSection 표시', () => {
    render(<PostCard post={basePost} />);

    expect(screen.queryByTestId('comment-section')).toBeNull();

    fireEvent.click(screen.getByText(/댓글 1/));

    expect(screen.getByTestId('comment-section')).toBeDefined();
  });

  it('이미지 첨부파일 렌더링', () => {
    const postWithImage: Post = {
      ...basePost,
      attachments: [{ id: 10, kind: 'image', object_key: 'uploads/img.jpg', created_at: '2026-01-01T00:00:00Z' }],
    };
    render(<PostCard post={postWithImage} />);

    const img = document.querySelector('img[src*="uploads/img.jpg"]');
    expect(img).not.toBeNull();
  });
});
