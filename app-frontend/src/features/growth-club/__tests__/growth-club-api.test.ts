import { growthClubApi } from '../api/growth-club';

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
    post: jest.fn(),
    delete: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';

const mockGet = apiClient.get as jest.Mock;
const mockPost = apiClient.post as jest.Mock;
const mockDelete = apiClient.delete as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('growthClubApi', () => {
  describe('getPosts', () => {
    it('기본 카테고리로 게시글 목록 조회', async () => {
      mockGet.mockResolvedValue({ data: [{ id: 1, title: 'test' }] });
      const result = await growthClubApi.getPosts();
      expect(mockGet).toHaveBeenCalledWith('/growth-club/posts', {
        params: { category: 'all' },
      });
      expect(result).toEqual([{ id: 1, title: 'test' }]);
    });

    it('카테고리 + 검색어로 조회', async () => {
      mockGet.mockResolvedValue({ data: [] });
      await growthClubApi.getPosts('free', '창업', 'title');
      expect(mockGet).toHaveBeenCalledWith('/growth-club/posts', {
        params: { category: 'free', search: '창업', search_type: 'title' },
      });
    });
  });

  describe('createPost', () => {
    it('FormData로 게시글 생성', async () => {
      const fd = new FormData();
      fd.append('title', 'test');
      mockPost.mockResolvedValue({ data: { id: 1 } });
      const result = await growthClubApi.createPost(fd);
      expect(mockPost).toHaveBeenCalledWith('/growth-club/posts', fd);
      expect(result).toEqual({ id: 1 });
    });
  });

  describe('addComment', () => {
    it('댓글 작성', async () => {
      mockPost.mockResolvedValue({ data: { id: 10 } });
      await growthClubApi.addComment(1, '좋은 글이네요');
      expect(mockPost).toHaveBeenCalledWith('/growth-club/comments', {
        post_id: 1,
        content: '좋은 글이네요',
        parent_id: undefined,
      });
    });

    it('답글 작성 (parent_id 포함)', async () => {
      mockPost.mockResolvedValue({ data: { id: 11 } });
      await growthClubApi.addComment(1, '답글', 5);
      expect(mockPost).toHaveBeenCalledWith('/growth-club/comments', {
        post_id: 1,
        content: '답글',
        parent_id: 5,
      });
    });
  });

  describe('likePost', () => {
    it('좋아요 토글 결과 반환', async () => {
      mockPost.mockResolvedValue({ data: { liked: true, likes_count: 3 } });
      const result = await growthClubApi.likePost(1);
      expect(mockPost).toHaveBeenCalledWith('/growth-club/posts/1/like');
      expect(result).toEqual({ liked: true, likes_count: 3 });
    });
  });

  describe('deletePost', () => {
    it('게시글 삭제', async () => {
      mockDelete.mockResolvedValue({ data: { status: 'success' } });
      await growthClubApi.deletePost(1);
      expect(mockDelete).toHaveBeenCalledWith('/growth-club/posts/1');
    });
  });

  describe('deleteComment', () => {
    it('댓글 삭제', async () => {
      mockDelete.mockResolvedValue({ data: { status: 'success' } });
      await growthClubApi.deleteComment(10);
      expect(mockDelete).toHaveBeenCalledWith('/growth-club/comments/10');
    });
  });

  describe('reportPost', () => {
    it('게시글 신고', async () => {
      mockPost.mockResolvedValue({ data: { status: 'success' } });
      await growthClubApi.reportPost(1, '광고');
      expect(mockPost).toHaveBeenCalledWith('/growth-club/posts/1/report', { reason: '광고' });
    });
  });

  describe('reportComment', () => {
    it('댓글 신고', async () => {
      mockPost.mockResolvedValue({ data: { status: 'success' } });
      await growthClubApi.reportComment(10, '폭언');
      expect(mockPost).toHaveBeenCalledWith('/growth-club/comments/10/report', { reason: '폭언' });
    });
  });
});
