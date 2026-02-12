
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

    it('renders dashboard with user name', () => {
        render(<DashboardView />);
        expect(screen.getByText(/Good Morning, Alex/i)).toBeInTheDocument();
    });

    it('renders current task progress card', () => {
        render(<DashboardView />);
        expect(screen.getByText(/Business Registration/i)).toBeInTheDocument();
        expect(screen.getByText(/20%/i)).toBeInTheDocument();
        // There are multiple "In Progress" texts (Header and Status), so we check if at least one exists
        const statusElements = screen.getAllByText(/In Progress/i);
        expect(statusElements.length).toBeGreaterThan(0);
    });

    it('renders growth club section', () => {
        render(<DashboardView />);
        expect(screen.getByText(/Growth Club/i)).toBeInTheDocument();
        expect(screen.getByText(/12 founders/i)).toBeInTheDocument();
    });

    it('renders roadmap stepper', () => {
        render(<DashboardView />);
        expect(screen.getByText(/Your Roadmap/i)).toBeInTheDocument();
        expect(screen.getByText(/Idea Validation/i)).toBeInTheDocument();
        expect(screen.getByText(/Tax Registration/i)).toBeInTheDocument();
    });

    it('renders stats', () => {
        render(<DashboardView />);
        expect(screen.getByText(/3 Days/i)).toBeInTheDocument();
        expect(screen.getByText(/8\/12/i)).toBeInTheDocument();
    });
});
