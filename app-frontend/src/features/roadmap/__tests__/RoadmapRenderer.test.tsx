
import { render, screen } from '@testing-library/react';
import RoadmapRenderer from '../components/RoadmapRenderer';
import { RoadmapNodeData } from '../types/roadmap';

const mockData: RoadmapNodeData = {
    id: 'root',
    title: '창업 준비',
    children: [
        {
            id: 'step-1',
            title: '사업자 등록',
            children: []
        }
    ]
};

describe('RoadmapRenderer', () => {
    test('renders root node title correctly', () => {
        render(<RoadmapRenderer data={mockData} />);
        expect(screen.getByText('창업 준비')).toBeInTheDocument();
    });

    test('renders child nodes recursively', () => {
        render(<RoadmapRenderer data={mockData} />);
        expect(screen.getByText('사업자 등록')).toBeInTheDocument();
    });
});
