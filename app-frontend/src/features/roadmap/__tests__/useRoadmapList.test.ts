import { renderHook, act } from '@testing-library/react';
import { useRoadmapList } from '../hooks/useRoadmapList';

jest.mock('../api', () => ({
  fetchRoadmapList: jest.fn(),
  deleteRoadmap: jest.fn(),
  updateRoadmapTitle: jest.fn(),
}));

import { fetchRoadmapList, deleteRoadmap, updateRoadmapTitle } from '../api';

const mockFetchList = fetchRoadmapList as jest.Mock;
const mockDelete = deleteRoadmap as jest.Mock;
const mockRename = updateRoadmapTitle as jest.Mock;

beforeEach(() => jest.clearAllMocks());

describe('useRoadmapList', () => {
  const sampleList = {
    items: [
      { id: 'r1', title: '카페 창업' },
      { id: 'r2', title: '음식점 창업' },
    ],
    total: 2,
  };

  it('loadList: 목록 조회 후 list/total 설정', async () => {
    mockFetchList.mockResolvedValue(sampleList);

    const { result } = renderHook(() => useRoadmapList());

    expect(result.current.loading).toBe(false);

    await act(async () => {
      await result.current.loadList();
    });

    expect(result.current.list).toEqual(sampleList.items);
    expect(result.current.total).toBe(2);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('loadList 실패 시 에러 설정', async () => {
    mockFetchList.mockRejectedValue(new Error('Network'));

    const { result } = renderHook(() => useRoadmapList());

    await act(async () => {
      await result.current.loadList();
    });

    expect(result.current.error).toBe('로드맵 목록을 불러오는데 실패했습니다.');
    expect(result.current.list).toEqual([]);
  });

  it('handleDelete: 삭제 후 목록 리로드', async () => {
    mockFetchList.mockResolvedValue(sampleList);
    mockDelete.mockResolvedValue(undefined);

    const { result } = renderHook(() => useRoadmapList());

    let ok: boolean;
    await act(async () => {
      ok = await result.current.handleDelete('r1');
    });

    expect(ok!).toBe(true);
    expect(mockDelete).toHaveBeenCalledWith('r1');
    expect(mockFetchList).toHaveBeenCalled();
  });

  it('handleRename: 이름 변경 후 목록 리로드', async () => {
    mockFetchList.mockResolvedValue(sampleList);
    mockRename.mockResolvedValue({ id: 'r1', title: '새 이름' });

    const { result } = renderHook(() => useRoadmapList());

    let ok: boolean;
    await act(async () => {
      ok = await result.current.handleRename('r1', '새 이름');
    });

    expect(ok!).toBe(true);
    expect(mockRename).toHaveBeenCalledWith('r1', '새 이름');
  });

  it('handleDelete 실패 시 에러 설정 + false 반환', async () => {
    mockDelete.mockRejectedValue(new Error('forbidden'));

    const { result } = renderHook(() => useRoadmapList());

    let ok: boolean;
    await act(async () => {
      ok = await result.current.handleDelete('r1');
    });

    expect(ok!).toBe(false);
    expect(result.current.error).toBe('로드맵 삭제에 실패했습니다.');
  });
});
