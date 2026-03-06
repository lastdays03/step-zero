import { renderHook, waitFor } from '@testing-library/react';
import { usePosts } from '../hooks/usePosts';

jest.mock('../api', () => ({
  growthClubApi: {
    getPosts: jest.fn(),
  },
}));

import { growthClubApi } from '../api';

const mockGetPosts = growthClubApi.getPosts as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('usePosts', () => {
  it('초기 로딩 후 게시글 목록 반환', async () => {
    const posts = [{ id: 1, title: '첫 글' }, { id: 2, title: '두번째' }];
    mockGetPosts.mockResolvedValue(posts);

    const { result } = renderHook(() => usePosts('all'));

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.posts).toEqual(posts);
    expect(result.current.error).toBeNull();
    expect(mockGetPosts).toHaveBeenCalledWith('all', undefined, undefined);
  });

  it('카테고리 + 검색어 전달', async () => {
    mockGetPosts.mockResolvedValue([]);

    const { result } = renderHook(() => usePosts('free', '창업', 'title'));

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(mockGetPosts).toHaveBeenCalledWith('free', '창업', 'title');
  });

  it('에러 시 error 상태 설정', async () => {
    mockGetPosts.mockRejectedValue(new Error('Network Error'));

    const { result } = renderHook(() => usePosts());

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBeInstanceOf(Error);
    expect(result.current.error?.message).toBe('Network Error');
    expect(result.current.posts).toEqual([]);
  });

  it('refetch로 다시 조회 가능', async () => {
    mockGetPosts.mockResolvedValueOnce([{ id: 1 }]).mockResolvedValueOnce([{ id: 1 }, { id: 2 }]);

    const { result } = renderHook(() => usePosts());

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.posts).toHaveLength(1);

    mockGetPosts.mockResolvedValueOnce([{ id: 1 }, { id: 2 }]);
    result.current.refetch();

    await waitFor(() => expect(result.current.posts).toHaveLength(2));
  });
});
