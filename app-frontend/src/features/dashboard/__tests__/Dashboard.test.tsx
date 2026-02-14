
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardView } from '../components/DashboardView';
import { useDashboard } from '../hooks/useDashboard';

// Mock the useDashboard hook
jest.mock('../hooks/useDashboard', () => ({
    useDashboard: jest.fn(),
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
        (useDashboard as jest.Mock).mockReturnValue({
            data: mockData,
            loading: false
        });
    });

    it('renders current phase title', () => {
        render(<DashboardView />);
        expect(screen.getByText(/Business Registration/i)).toBeInTheDocument();
    });

    it('renders current task progress card', () => {
        render(<DashboardView />);
        expect(screen.getByText(/20%/i)).toBeInTheDocument();
        expect(screen.getByText(/현재 진행 단계/i)).toBeInTheDocument();
    });

    it('renders growth club section', () => {
        render(<DashboardView />);
        expect(screen.getByText(/LIVE: GROWTH CLUB/i)).toBeInTheDocument();
        expect(screen.getByText(/12명의 동료 창업자와/i)).toBeInTheDocument();
    });

    it('renders roadmap stepper', () => {
        render(<DashboardView />);
        expect(screen.getByText(/나의 로드맵/i)).toBeInTheDocument();
        expect(screen.getByText(/Idea Validation/i)).toBeInTheDocument();
        expect(screen.getByText(/Tax Registration/i)).toBeInTheDocument();
    });

    it('renders stats', () => {
        render(<DashboardView />);
        const dayTexts = screen.getAllByText(/3일/i);
        expect(dayTexts.length).toBeGreaterThan(0);
        expect(screen.getByText(/8\/12/i)).toBeInTheDocument();
    });
});
