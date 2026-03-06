import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { RoadmapSwitcher } from '../components/RoadmapSwitcher';
import type { RoadmapSummary } from '../types/roadmap';

// ---- Mocks ----

// Radix Popover: open 상태면 children 렌더, 아니면 숨김
jest.mock('@/components/ui/popover', () => ({
  Popover: ({ children, open }: { children: React.ReactNode; open: boolean }) =>
    open ? <div data-testid="popover">{children}</div> : null,
  PopoverTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  PopoverContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

jest.mock('@/components/ui/dropdown-menu', () => ({
  DropdownMenu: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  DropdownMenuContent: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
  DropdownMenuItem: ({ children, onClick }: { children: React.ReactNode; onClick?: React.MouseEventHandler }) => (
    <button onClick={onClick}>{children}</button>
  ),
  DropdownMenuTrigger: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/components/ui/badge', () => ({
  Badge: ({ children }: { children: React.ReactNode }) => <span>{children}</span>,
}));

jest.mock('@/components/ui/button', () => ({
  Button: ({ children, onClick, ...rest }: React.ButtonHTMLAttributes<HTMLButtonElement>) => (
    <button onClick={onClick} {...rest}>{children}</button>
  ),
}));

jest.mock('@/components/ui/separator', () => ({
  Separator: () => <hr />,
}));

jest.mock('@/components/ui/progress', () => ({
  Progress: ({ value }: { value: number }) => <div data-testid="progress" data-value={value} />,
}));

jest.mock('../components/RoadmapDeleteDialog', () => ({
  RoadmapDeleteDialog: () => null,
}));

jest.mock('../components/RoadmapRenameDialog', () => ({
  RoadmapRenameDialog: () => null,
}));

const sampleRoadmaps: RoadmapSummary[] = [
  { roadmap_id: 'r1', title: '카페 창업', business_type: '카페', location: '서울', created_at: '2026-01-01', progress: 40, total_steps: 5, completed_steps: 2 },
  { roadmap_id: 'r2', title: '음식점 창업', business_type: '음식점', location: '부산', created_at: '2026-01-02', progress: 80, total_steps: 5, completed_steps: 4 },
];

const defaultProps = {
  roadmaps: sampleRoadmaps,
  activeRoadmapId: 'r1',
  onSelect: jest.fn(),
  onDelete: jest.fn(),
  onRename: jest.fn(),
  onCreateNew: jest.fn(),
  open: true,
  onOpenChange: jest.fn(),
};

beforeEach(() => jest.clearAllMocks());

describe('RoadmapSwitcher', () => {
  it('로드맵 목록 렌더링', () => {
    render(<RoadmapSwitcher {...defaultProps} />);

    expect(screen.getByText('카페 창업')).toBeDefined();
    expect(screen.getByText('음식점 창업')).toBeDefined();
    expect(screen.getByText('나의 로드맵')).toBeDefined();
  });

  it('로드맵 개수 배지 표시', () => {
    render(<RoadmapSwitcher {...defaultProps} />);

    expect(screen.getByText('2')).toBeDefined();
  });

  it('로드맵 클릭 시 onSelect + onOpenChange 호출', () => {
    render(<RoadmapSwitcher {...defaultProps} />);

    fireEvent.click(screen.getByText('음식점 창업'));

    expect(defaultProps.onSelect).toHaveBeenCalledWith('r2');
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it('새 로드맵 만들기 버튼 클릭', () => {
    render(<RoadmapSwitcher {...defaultProps} />);

    fireEvent.click(screen.getByText('새 로드맵 만들기'));

    expect(defaultProps.onCreateNew).toHaveBeenCalled();
    expect(defaultProps.onOpenChange).toHaveBeenCalledWith(false);
  });

  it('빈 목록일 때 안내 메시지', () => {
    render(<RoadmapSwitcher {...defaultProps} roadmaps={[]} />);

    expect(screen.getByText('로드맵이 없습니다.')).toBeDefined();
  });

  it('open=false면 팝오버 비표시', () => {
    render(<RoadmapSwitcher {...defaultProps} open={false} />);

    expect(screen.queryByText('나의 로드맵')).toBeNull();
  });
});
