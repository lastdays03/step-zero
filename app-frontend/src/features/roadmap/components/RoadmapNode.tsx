
import { RoadmapNodeData } from '../types/roadmap';

interface RoadmapNodeProps {
    data: RoadmapNodeData;
}

const RoadmapNode = ({ data }: RoadmapNodeProps) => {
    return (
        <div className="border p-4 m-2 rounded shadow-sm">
            <h3 className="font-bold">{data.title}</h3>
            {data.children && data.children.length > 0 && (
                <div className="ml-4 border-l pl-4">
                    {data.children.map((child) => (
                        <RoadmapNode key={child.id} data={child} />
                    ))}
                </div>
            )}
        </div>
    );
};

export default RoadmapNode;
