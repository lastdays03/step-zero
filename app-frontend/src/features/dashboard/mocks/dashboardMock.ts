
import { DashboardData } from '../hooks/useDashboard';

export const MOCK_DASHBOARD_DATA: DashboardData = {
    user_name: "Alex",
    current_phase: {
        title: "사업자 등록",
        progress: 20,
        status: "진행 중"
    },
    roadmap: [
        { title: "아이디어 검증", status: "completed", date: "완료됨" },
        { title: "임대차 계약", status: "completed", date: "완료됨" },
        { title: "사업자 등록", status: "current", date: "현재 진행" },
        { title: "은행 계좌", status: "locked", date: "대기 중" },
        { title: "팀 채용", status: "locked", date: "대기 중" }
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

/**
 * Simulates an API call to fetch dashboard data
 */
export const fetchDashboardMock = (): Promise<DashboardData> => {
    return new Promise((resolve) => {
        setTimeout(() => {
            resolve(MOCK_DASHBOARD_DATA);
        }, 800);
    });
};
