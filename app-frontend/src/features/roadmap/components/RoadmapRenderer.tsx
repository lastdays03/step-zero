
import { RoadmapNodeData } from '../types/roadmap';
import RoadmapNode from './RoadmapNode';

interface RoadmapRendererProps {
    data: RoadmapNodeData;
}

const RoadmapRenderer = ({ data }: RoadmapRendererProps) => {
    return (
        <div className="w-full">
            <RoadmapNode data={data} />
        </div>
    );
};

export default RoadmapRenderer;
