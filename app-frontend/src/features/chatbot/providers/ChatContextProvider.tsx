"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { apiClient } from "@/lib/api-client";

// ---- Types ----

interface RoadmapStep {
  id: number;
  title: string;
  status: string;
}

interface RoadmapDetail {
  steps: RoadmapStep[];
}

interface ChatContextValue {
  roadmapId: string | null;
  stepId: number | null;
  stepTitle: string | null;
  hasCoachContext: boolean;
  setCoachContext: (roadmapId: string, stepId: number, stepTitle: string) => void;
  clearCoachContext: () => void;
  isPanelOpen: boolean;
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;
}

const ACTIVE_ROADMAP_KEY = "stepzero_active_roadmap_id";

// ---- Context ----

const ChatContext = createContext<ChatContextValue | null>(null);

// ---- Provider ----

interface ChatContextProviderProps {
  children: ReactNode;
}

export function ChatContextProvider({ children }: ChatContextProviderProps) {
  const [roadmapId, setRoadmapId] = useState<string | null>(null);
  const [stepId, setStepId] = useState<number | null>(null);
  const [stepTitle, setStepTitle] = useState<string | null>(null);
  const [isPanelOpen, setIsPanelOpen] = useState(false);

  const hasCoachContext = roadmapId !== null && stepId !== null;

  const setCoachContext = useCallback(
    (newRoadmapId: string, newStepId: number, newStepTitle: string) => {
      setRoadmapId(newRoadmapId);
      setStepId(newStepId);
      setStepTitle(newStepTitle);
    },
    [],
  );

  const clearCoachContext = useCallback(() => {
    setRoadmapId(null);
    setStepId(null);
    setStepTitle(null);
  }, []);

  const openPanel = useCallback(() => setIsPanelOpen(true), []);
  const closePanel = useCallback(() => setIsPanelOpen(false), []);
  const togglePanel = useCallback(() => setIsPanelOpen((prev) => !prev), []);

  // localStorage의 active roadmap 변경 감지 (다른 탭에서 변경 시)
  useEffect(() => {
    const handleStorage = async (e: StorageEvent) => {
      if (e.key !== ACTIVE_ROADMAP_KEY) return;

      const newRoadmapId = e.newValue;
      if (!newRoadmapId) {
        clearCoachContext();
        return;
      }

      // 로드맵 정보 조회 → IN_PROGRESS 단계 자동 선택
      try {
        const res = await apiClient.get<RoadmapDetail>(
          `/roadmaps/${newRoadmapId}`,
        );
        const steps = res.data.steps ?? [];
        const inProgressStep = steps.find((s) => s.status === "IN_PROGRESS");

        if (inProgressStep) {
          setCoachContext(
            newRoadmapId,
            inProgressStep.id,
            inProgressStep.title,
          );
        } else {
          setRoadmapId(newRoadmapId);
          setStepId(null);
          setStepTitle(null);
        }
      } catch {
        // API 실패 시 roadmapId만 설정
        setRoadmapId(newRoadmapId);
        setStepId(null);
        setStepTitle(null);
      }
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [setCoachContext, clearCoachContext]);

  return (
    <ChatContext.Provider
      value={{
        roadmapId,
        stepId,
        stepTitle,
        hasCoachContext,
        setCoachContext,
        clearCoachContext,
        isPanelOpen,
        openPanel,
        closePanel,
        togglePanel,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

// ---- Hook ----

export function useChatContext(): ChatContextValue {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error("useChatContext must be used within ChatContextProvider");
  }
  return ctx;
}
