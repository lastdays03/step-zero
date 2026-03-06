import { renderHook, act } from '@testing-library/react';
import { useRoadmapJob, RoadmapIntakePayload, RoadmapJobStatus } from '../hooks/useRoadmapJob';

jest.mock('@/lib/api-client', () => ({
  apiClient: {
    post: jest.fn(),
    get: jest.fn(),
  },
}));

import { apiClient } from '@/lib/api-client';

const mockPost = apiClient.post as jest.Mock;
const mockGet = apiClient.get as jest.Mock;

const samplePayload: RoadmapIntakePayload = {
  business_type: '카페',
  location: '서울',
  description: '커피숍 창업',
  startup_type: '개인',
  startup_method: '신규',
  open_timeline: '3개월',
  budget_range: '5000만원',
  additional_notes: '',
  goal_horizon_days: 90,
  experience_level: '초보',
};

const queuedJob: RoadmapJobStatus = {
  job_id: 'job-1',
  status: 'QUEUED',
  stage: 'queued',
  progress: 0,
};

const succeededJob: RoadmapJobStatus = {
  job_id: 'job-1',
  status: 'SUCCEEDED',
  stage: 'completed',
  progress: 100,
  roadmap_id: 'roadmap-1',
};

beforeEach(() => jest.clearAllMocks());

describe('useRoadmapJob', () => {
  it('startJob: 잡 생성 후 job_id 반환', async () => {
    mockPost.mockResolvedValue({ data: queuedJob });

    const { result } = renderHook(() => useRoadmapJob());

    let jobId: string;
    await act(async () => {
      jobId = await result.current.startJob(samplePayload);
    });

    expect(mockPost).toHaveBeenCalledWith('/roadmaps/jobs', samplePayload);
    expect(jobId!).toBe('job-1');
    expect(result.current.job).toEqual(queuedJob);
  });

  it('fetchJob: 상태 폴링 후 job 업데이트', async () => {
    mockGet.mockResolvedValue({ data: succeededJob });

    const { result } = renderHook(() => useRoadmapJob());

    let status: RoadmapJobStatus;
    await act(async () => {
      status = await result.current.fetchJob('job-1');
    });

    expect(mockGet).toHaveBeenCalledWith('/roadmaps/jobs/job-1');
    expect(status!.status).toBe('SUCCEEDED');
    expect(result.current.job?.roadmap_id).toBe('roadmap-1');
  });

  it('fetchResult: 결과 조회', async () => {
    mockGet.mockResolvedValue({ data: { job_id: 'job-1', status: 'SUCCEEDED', roadmap_id: 'r-1' } });

    const { result } = renderHook(() => useRoadmapJob());

    let res: { roadmap_id?: string | null };
    await act(async () => {
      res = await result.current.fetchResult('job-1');
    });

    expect(mockGet).toHaveBeenCalledWith('/roadmaps/jobs/job-1/result');
    expect(res!.roadmap_id).toBe('r-1');
  });

  it('setError: 에러 수동 설정', () => {
    const { result } = renderHook(() => useRoadmapJob());
    act(() => result.current.setError('timeout'));
    expect(result.current.error).toBe('timeout');
  });
});
