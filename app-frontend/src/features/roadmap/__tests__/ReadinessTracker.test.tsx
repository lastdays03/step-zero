import React from 'react';
import { render, screen } from '@testing-library/react';
import { ReadinessTracker } from '../components/ReadinessTracker';

describe('ReadinessTracker', () => {
  it('5단계 레벨 모두 렌더링', () => {
    const { container } = render(<ReadinessTracker progressPercent={0} />);

    // title 속성으로 5개 레벨 확인
    const levels = container.querySelectorAll('[title]');
    expect(levels).toHaveLength(5);
  });

  it('진행률 0%: 1단계(아이디어) 활성', () => {
    render(<ReadinessTracker progressPercent={0} />);

    // 현재 레벨은 emoji 표시, 이전 레벨은 ✓, 미래는 ○
    expect(screen.getByText('🌱')).toBeDefined();
  });

  it('진행률 50%: 3단계(서류 준비 중) 활성', () => {
    render(<ReadinessTracker progressPercent={50} />);

    expect(screen.getByText('📝')).toBeDefined();
    // 이전 단계들은 ✓
    const checks = screen.getAllByText('✓');
    expect(checks.length).toBeGreaterThanOrEqual(2);
  });

  it('진행률 100%: 5단계(창업 준비 완료) 활성', () => {
    render(<ReadinessTracker progressPercent={100} />);

    expect(screen.getByText('🚀')).toBeDefined();
    // 이전 4단계 모두 ✓
    const checks = screen.getAllByText('✓');
    expect(checks).toHaveLength(4);
  });

  it('미래 레벨에 ○ 표시', () => {
    render(<ReadinessTracker progressPercent={0} />);

    const circles = screen.getAllByText('○');
    expect(circles).toHaveLength(4); // level 2-5
  });
});
