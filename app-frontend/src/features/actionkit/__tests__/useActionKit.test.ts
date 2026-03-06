import { renderHook, waitFor } from '@testing-library/react';
import { useActionKit } from '../hooks/useActionKit';

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    get: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';

const mockGet = apiClient.get as jest.Mock;
let consoleErrorSpy: jest.SpyInstance;

beforeEach(() => {
  jest.clearAllMocks();
  consoleErrorSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
});

afterEach(() => {
  consoleErrorSpy.mockRestore();
});

describe('useActionKit', () => {
  it('성공 시 data 반환, loading false', async () => {
    const kitData = { all: { title: '전체', items: [] } };
    mockGet.mockResolvedValue({ data: kitData });

    const { result } = renderHook(() => useActionKit());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(kitData);
    expect(result.current.error).toBeNull();
    expect(mockGet).toHaveBeenCalledWith('/actionkits/kits');
  });

  it('실패 시 error 설정', async () => {
    mockGet.mockRejectedValue(new Error('Network Error'));

    const { result } = renderHook(() => useActionKit());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBe('액션 키트 데이터를 불러오는 중 오류가 발생했습니다.');
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Failed to load action kit data:',
      expect.any(Error),
    );
  });
});
