
import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardView } from '../components/DashboardView';
import { useDashboard } from '../hooks/useDashboard';
import { apiClient } from '../../../lib/api-client';

// Mock the useDashboard hook
jest.mock('../hooks/useDashboard', () => ({
    useDashboard: jest.fn(),
}));
jest.mock('../../../providers/AuthProvider', () => ({
    useAuth: () => ({
        isLoggedIn: true,
        user: { username: 'Alex' },
    }),
}));
jest.mock('next/navigation', () => ({
    useRouter: () => ({
        push: jest.fn(),
    }),
}));
jest.mock('../../../lib/api-client', () => ({
    apiClient: {
        get: jest.fn(),
        post: jest.fn(),
    },
}));
jest.mock('../../../features/roadmap/api', () => ({
    fetchRoadmapDetail: jest.fn(),
}));
jest.mock('../../../features/roadmap/components', () => ({
    RoadmapGenerationPanel: () => <div data-testid="generation-panel" />,
    computeEndowedProgress: (completed: number, total: number) => ({
        display: Math.round(((completed + 3) / (total + 3)) * 100),
        actual: total > 0 ? Math.round((completed / total) * 100) : 0,
        endowedSteps: 3,
        totalWithEndowed: total + 3,
    }),
    computeReadinessLevel: (pct: number) => {
        if (pct >= 90) return { level: 5, emoji: '🚀', label: '창업 준비 완료', description: '' };
        if (pct >= 65) return { level: 4, emoji: '✅', label: '인허가 완료', description: '' };
        if (pct >= 35) return { level: 3, emoji: '📝', label: '서류 준비 중', description: '' };
        if (pct >= 10) return { level: 2, emoji: '📋', label: '준비 착수', description: '' };
        return { level: 1, emoji: '🌱', label: '아이디어', description: '' };
    },
}));

const mockData = {
    user_name: "Alex",
    current_phase: {
        title: "Business Registration",
        progress: 20,
        status: "IN_PROGRESS"
    },
    roadmap: [
        { title: "Idea Validation", status: "COMPLETED", date: "Jan 12" },
        { title: "Sign Lease", status: "COMPLETED", date: "Jan 24" },
        { title: "Tax Registration", status: "CURRENT", date: "Current Task" },
        { title: "Bank Account", status: "LOCKED", date: "Estimated Feb 10" }
    ],
    stats: {
        days_left: 3,
        tasks_completed: 8,
        total_tasks: 12
    },
    growth_club: {
        founders_online: 12
    }
};

describe('DashboardView', () => {
    beforeEach(() => {
        jest.mocked(apiClient.get).mockResolvedValue({
            data: {
                roadmap_id: "r-1",
                title: "테스트 로드맵",
                steps: [
                    {
                        id: 1,
                        title: "현재 단계",
                        status: "IN_PROGRESS",
                        detail: {
                            id: 1,
                            phase: "Business Registration",
                            objective: "현재 단계 목표",
                            estimated_days: 3,
                            actions: [
                                {
                                    id: 101,
                                    action_type: "DOCUMENT",
                                    title: "사업자등록 신청서",
                                    description: "필수",
                                    source_url: "https://gov.kr/doc-1.pdf",
                                    metadata_json: { completed: false },
                                },
                            ],
                        },
                    },
                    {
                        id: 2,
                        title: "다음 단계",
                        status: "PENDING",
                        detail: {
                            id: 2,
                            phase: "Opening",
                            objective: "다음 단계 목표",
                            estimated_days: 3,
                            actions: [
                                {
                                    id: 201,
                                    action_type: "DOCUMENT",
                                    title: "노출되면 안 되는 다음 단계 문서",
                                    description: "다음 단계",
                                    source_url: "https://gov.kr/doc-2.pdf",
                                    metadata_json: { completed: false },
                                },
                            ],
                        },
                    },
                ],
            },
        });
        jest.mocked(useDashboard).mockReturnValue({
            data: mockData,
            loading: false,
            reload: jest.fn(),
        });
    });

    it('renders current phase title', async () => {
        render(<DashboardView />);
        await waitFor(() => {
            expect(screen.getByText(/Business Registration/i)).toBeInTheDocument();
        });
    });

    it('renders current task progress card', async () => {
        render(<DashboardView />);
        await waitFor(() => {
            expect(screen.getByText(/현재 진행 단계/i)).toBeInTheDocument();
        });
    });

    it('renders growth club section', async () => {
        render(<DashboardView />);
        await waitFor(() => {
            expect(screen.getByText(/LIVE: GROWTH CLUB/i)).toBeInTheDocument();
            expect(screen.getByText(/12명의 동료 창업자와/i)).toBeInTheDocument();
        });
    });

    it('renders roadmap stepper', async () => {
        render(<DashboardView />);
        await waitFor(() => {
            expect(screen.getByText(/나의 로드맵/i)).toBeInTheDocument();
            expect(screen.getByText(/Idea Validation/i)).toBeInTheDocument();
            expect(screen.getByText(/Tax Registration/i)).toBeInTheDocument();
        });
    });

    it('renders stats', async () => {
        render(<DashboardView />);
        await waitFor(() => {
            expect(screen.getByText(/D-3/i)).toBeInTheDocument();
            expect(screen.getByText(/8\/12/i)).toBeInTheDocument();
        });
    });

    it('shows only current-step documents in dashboard card', async () => {
        render(<DashboardView />);
        expect(await screen.findByText(/사업자등록 신청서/i)).toBeInTheDocument();
        expect(screen.queryByText(/노출되면 안 되는 다음 단계 문서/i)).not.toBeInTheDocument();
    });
});
