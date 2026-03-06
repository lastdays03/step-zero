import { renderHook, waitFor, act } from '@testing-library/react';
import { useActiveRoadmap } from '../hooks/useActiveRoadmap';

jest.mock('../api', () => ({
  fetchRoadmapDetail: jest.fn(),
}));

import { fetchRoadmapDetail } from '../api';

const mockFetchDetail = fetchRoadmapDetail as jest.Mock;

const STORAGE_KEY = 'stepzero_active_roadmap_id';

beforeEach(() => {
  jest.clearAllMocks();
  localStorage.clear();
});

describe('useActiveRoadmap', () => {
  const detail = {
    id: 'r1',
    title: '카페 창업 로드맵',
    steps: [{ id: 1, title: '사업계획서', status: 'IN_PROGRESS' }],
  };

  it('localStorage에 저장된 ID로 마운트 시 상세 로드', async () => {
    localStorage.setItem(STORAGE_KEY, 'r1');
    mockFetchDetail.mockResolvedValue(detail);

    const { result } = renderHook(() => useActiveRoadmap());

    await waitFor(() => {
      expect(result.current.activeRoadmapId).toBe('r1');
    });

    expect(result.current.activeRoadmap).toEqual(detail);
    expect(result.current.loading).toBe(false);
  });

  it('setActiveRoadmap: localStorage 저장 + 상세 로드', async () => {
    mockFetchDetail.mockResolvedValue(detail);

    const { result } = renderHook(() => useActiveRoadmap());

    await act(async () => {
      await result.current.setActiveRoadmap('r1');
    });

    expect(localStorage.getItem(STORAGE_KEY)).toBe('r1');
    expect(result.current.activeRoadmapId).toBe('r1');
    expect(result.current.activeRoadmap).toEqual(detail);
  });

  it('clearActiveRoadmap: localStorage 제거 + 상태 초기화', async () => {
    localStorage.setItem(STORAGE_KEY, 'r1');
    mockFetchDetail.mockResolvedValue(detail);

    const { result } = renderHook(() => useActiveRoadmap());

    await waitFor(() => expect(result.current.activeRoadmapId).toBe('r1'));

    act(() => {
      result.current.clearActiveRoadmap();
    });

    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
    expect(result.current.activeRoadmapId).toBeNull();
    expect(result.current.activeRoadmap).toBeNull();
  });

  it('404 에러 시 localStorage 클리어 + 에러 없음', async () => {
    localStorage.setItem(STORAGE_KEY, 'deleted');
    const err = { response: { status: 404 } };
    mockFetchDetail.mockRejectedValue(err);

    const { result } = renderHook(() => useActiveRoadmap());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.activeRoadmapId).toBeNull();
    expect(result.current.activeRoadmap).toBeNull();
    expect(result.current.error).toBeNull();
    expect(localStorage.getItem(STORAGE_KEY)).toBeNull();
  });

  it('비-404 에러 시 에러 메시지 설정', async () => {
    localStorage.setItem(STORAGE_KEY, 'r1');
    mockFetchDetail.mockRejectedValue(new Error('Server Error'));

    const { result } = renderHook(() => useActiveRoadmap());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe('로드맵을 불러오는데 실패했습니다.');
  });
});
