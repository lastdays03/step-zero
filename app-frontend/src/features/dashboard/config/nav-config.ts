import { LayoutDashboard, Map, Briefcase, Users, Shield } from 'lucide-react';
import type { LucideIcon } from 'lucide-react';

export interface NavItem {
    icon: LucideIcon;
    label: string;
    mobileLabel: string;
    caption: string;
    href: string;
    badge?: string;
    requiresOps?: boolean;
}

export const NAV_ITEMS: NavItem[] = [
    { icon: LayoutDashboard, label: '대시보드', mobileLabel: '홈', caption: '현재 진행 상황 한눈에', href: '/dashboard' },
    { icon: Map, label: '나의 로드맵', mobileLabel: '로드맵', caption: 'AI 맞춤 창업 단계', href: '/roadmap' },
    { icon: Briefcase, label: '액션 키트', mobileLabel: '서류함', caption: '필요 서류 · 체크리스트', href: '/actionkit' },
    { icon: Users, label: '그로스 클럽', mobileLabel: '커뮤니티', caption: '창업자 커뮤니티', href: '/growth-club' },
    { icon: Shield, label: '운영 콘솔', mobileLabel: '운영', caption: '관리자 전용', href: '/ops', requiresOps: true },
];

export function getNavItems(canAccessOps: boolean): NavItem[] {
    return NAV_ITEMS.filter((item) => !item.requiresOps || canAccessOps);
}
