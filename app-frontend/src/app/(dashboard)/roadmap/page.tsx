"use client";

import { useCallback, useEffect, useState } from "react";
import { ArrowLeft } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { RoadmapExecutionView } from "@/features/roadmap/components/RoadmapExecutionView";
import { RoadmapGenerationPanel } from "@/features/roadmap/components";
import { RoadmapHeader } from "@/features/roadmap/components/RoadmapHeader";
import { RoadmapSwitcher } from "@/features/roadmap/components/RoadmapSwitcher";
import { useActiveRoadmap } from "@/features/roadmap/hooks/useActiveRoadmap";
import { useRoadmapList } from "@/features/roadmap/hooks/useRoadmapList";
import { derivePhaseGroups } from "@/features/roadmap/components/roadmap-utils";
import { useAuth } from "@/providers/AuthProvider";
import { Button } from "@/components/ui/button";

type PageMode = "loading" | "empty" | "viewing" | "creating";

export default function RoadmapPage() {
    const { isLoggedIn } = useAuth();
    const [pageMode, setPageMode] = useState<PageMode>("loading");
    const [switcherOpen, setSwitcherOpen] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [generationError, setGenerationError] = useState<string | null>(null);
    const [updatingStepId, setUpdatingStepId] = useState<number | null>(null);
    const [updatingActionId, setUpdatingActionId] = useState<number | null>(null);

    const {
        activeRoadmapId,
        activeRoadmap,
        loading: activeLoading,
        setActiveRoadmap,
        clearActiveRoadmap,
        reloadActiveRoadmap,
    } = useActiveRoadmap();

    const {
        list: roadmapList,
        loading: listLoading,
        loadList,
        handleDelete,
        handleRename,
    } = useRoadmapList();

    // Initial load: fetch list + resolve initial page mode
    useEffect(() => {
        void loadList();
    }, [loadList]);

    useEffect(() => {
        // Don't override user-initiated modes
        if (pageMode === "creating") return;

        // Wait for both list and active roadmap hooks to settle
        if (listLoading || activeLoading) {
            setPageMode("loading");
            return;
        }

        if (roadmapList.length === 0) {
            setPageMode("empty");
            return;
        }

        if (activeRoadmap) {
            setPageMode("viewing");
            return;
        }

        // Active roadmap not loaded (localStorage empty or 404) → pick first
        if (!activeRoadmapId && roadmapList.length > 0) {
            void setActiveRoadmap(roadmapList[0].roadmap_id);
            return;
        }

        // Still waiting for active roadmap detail to load
        setPageMode("loading");
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [
        listLoading,
        activeLoading,
        roadmapList,
        activeRoadmap,
        activeRoadmapId,
        setActiveRoadmap,
    ]);

    // --- Event handlers ---

    const handleSwitcherSelect = useCallback(
        (id: string) => {
            void setActiveRoadmap(id);
        },
        [setActiveRoadmap],
    );

    const handleSwitcherDelete = useCallback(
        async (id: string) => {
            const ok = await handleDelete(id);
            if (!ok) return;

            if (id === activeRoadmapId) {
                // Deleted the active roadmap: pick another or go empty
                const remaining = roadmapList.filter(
                    (r) => r.roadmap_id !== id,
                );
                if (remaining.length > 0) {
                    void setActiveRoadmap(remaining[0].roadmap_id);
                } else {
                    clearActiveRoadmap();
                    setPageMode("empty");
                }
            }
        },
        [
            handleDelete,
            activeRoadmapId,
            roadmapList,
            setActiveRoadmap,
            clearActiveRoadmap,
        ],
    );

    const handleSwitcherRename = useCallback(
        async (id: string, newTitle: string) => {
            const ok = await handleRename(id, newTitle);
            if (!ok) return;
            if (id === activeRoadmapId) {
                void reloadActiveRoadmap();
            }
        },
        [handleRename, activeRoadmapId, reloadActiveRoadmap],
    );

    const handleCreateNew = useCallback(() => {
        setPageMode("creating");
    }, []);

    const handleGenerated = useCallback(
        async (roadmapId: string | number) => {
            const id = String(roadmapId);
            await setActiveRoadmap(id);
            await loadList();
            setPageMode("viewing");
        },
        [setActiveRoadmap, loadList],
    );

    const handleCreateCancel = useCallback(() => {
        if (roadmapList.length > 0) {
            setPageMode("viewing");
        } else {
            setPageMode("empty");
        }
    }, [roadmapList]);

    const handleStepStatusChange = async (
        stepId: number,
        status: "IN_PROGRESS" | "COMPLETED",
    ) => {
        setUpdatingStepId(stepId);
        setGenerationError(null);
        try {
            await apiClient.patch(`/roadmaps/tasks/${stepId}`, { status });
            await reloadActiveRoadmap();
        } catch (e) {
            console.error(e);
            setGenerationError(
                "단계 상태를 변경하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            );
        } finally {
            setUpdatingStepId(null);
        }
    };

    const handleActionCompletionChange = async (
        stepId: number,
        actionId: number,
        completed: boolean,
    ) => {
        setUpdatingActionId(actionId);
        setGenerationError(null);
        try {
            await apiClient.patch(
                `/roadmaps/tasks/${stepId}/actions/${actionId}`,
                { completed },
            );
            await reloadActiveRoadmap();
        } catch (e) {
            console.error(e);
            setGenerationError(
                "체크리스트 상태를 저장하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            );
        } finally {
            setUpdatingActionId(null);
        }
    };

    // --- Render ---

    if (pageMode === "loading") {
        return (
            <section className="rounded-2xl border border-slate-200 bg-white p-8">
                <h1 className="text-2xl font-bold text-slate-900">로드맵</h1>
                <p className="mt-2 text-sm text-slate-600">
                    로드맵 상태를 확인하는 중입니다...
                </p>
            </section>
        );
    }

    if (error) {
        return (
            <section className="rounded-2xl border border-red-200 bg-white p-8">
                <h1 className="text-2xl font-bold text-slate-900">로드맵</h1>
                <p className="mt-2 text-sm text-red-600">{error}</p>
                <button
                    type="button"
                    onClick={() => {
                        setError(null);
                        void loadList();
                    }}
                    className="mt-4 rounded-lg bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
                >
                    다시 시도
                </button>
            </section>
        );
    }

    if (pageMode === "empty") {
        return (
            <RoadmapGenerationPanel
                isAuthenticated={isLoggedIn}
                onRefresh={() => void loadList()}
                onGenerated={handleGenerated}
            />
        );
    }

    if (pageMode === "creating") {
        return (
            <div>
                <Button
                    variant="ghost"
                    className="mb-4 gap-1 text-slate-500 hover:text-slate-700"
                    onClick={handleCreateCancel}
                >
                    <ArrowLeft className="h-4 w-4" />
                    로드맵으로 돌아가기
                </Button>
                <RoadmapGenerationPanel
                    isAuthenticated={isLoggedIn}
                    onGenerated={handleGenerated}
                />
            </div>
        );
    }

    // pageMode === "viewing"
    if (!activeRoadmap) return null;

    const phaseGroups = derivePhaseGroups(activeRoadmap.steps);
    const currentPhase = phaseGroups.find((g) => g.state === "CURRENT");

    return (
        <div className="space-y-4">
            {generationError ? (
                <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
                    {generationError}
                </p>
            ) : null}

            <RoadmapHeader
                title={activeRoadmap.title}
                currentPhaseName={currentPhase?.phase ?? null}
                onSwitcherToggle={() => setSwitcherOpen((prev) => !prev)}
                roadmapCount={roadmapList.length}
            />

            <RoadmapSwitcher
                roadmaps={roadmapList}
                activeRoadmapId={activeRoadmapId}
                onSelect={handleSwitcherSelect}
                onDelete={handleSwitcherDelete}
                onRename={handleSwitcherRename}
                onCreateNew={handleCreateNew}
                open={switcherOpen}
                onOpenChange={setSwitcherOpen}
            />

            <RoadmapExecutionView
                data={activeRoadmap}
                onStepStatusChange={handleStepStatusChange}
                onActionCompletionChange={handleActionCompletionChange}
                updatingStepId={updatingStepId}
                updatingActionId={updatingActionId}
                hideHeader
            />
        </div>
    );
}
