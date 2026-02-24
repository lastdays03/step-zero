"use client";

interface RoadmapHeaderProps {
    title: string;
    currentPhaseName: string | null;
}

export function RoadmapHeader({
    title,
    currentPhaseName,
}: RoadmapHeaderProps) {
    return (
        <div className="mb-10">
            <h1 className="text-3xl md:text-4xl font-bold text-slate-900 mb-3">
                나의 로드맵
            </h1>
            <p className="text-slate-500 text-lg">
                {title}
                {currentPhaseName ? (
                    <>
                        , 현재{" "}
                        <span className="text-[#36a4f2] font-semibold">
                            {currentPhaseName}
                        </span>{" "}
                        단계 진행 중입니다.
                    </>
                ) : null}
            </p>
        </div>
    );
}
