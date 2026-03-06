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

// ------------------------------------------------------------------ //
//  내부 타입 (로드맵 API 응답 서브셋)
// ------------------------------------------------------------------ //

interface RoadmapStepBrief {
  id: number;
  title: string;
  status: string;
}

interface RoadmapDetailBrief {
  steps: RoadmapStepBrief[];
}

// ------------------------------------------------------------------ //
//  Public 타입
// ------------------------------------------------------------------ //

export interface RoadmapContext {
  roadmapId: string;
  stepId: number | null;
  stepTitle: string | null;
}

export interface SessionPreview {
  id: string;
  title?: string | null;
  message_count?: number;
  roadmap_id?: string | null;
  step_id?: number | null;
  created_at?: string;
  updated_at: string;
}

export interface ChatProviderValue {
  /** 현재 활성 세션 ID */
  currentSessionId: string | null;
  setCurrentSessionId: (id: string | null) => void;
  refreshSessionList: () => void;
  sessionListVersion: number;
  publishSessionPreview: (session: SessionPreview) => void;
  sessionPreview: SessionPreview | null;
  sessionPreviewVersion: number;

  /** 로드맵 컨텍스트 (활성 로드맵의 IN_PROGRESS 단계) */
  roadmapContext: RoadmapContext | null;
  hasRoadmapContext: boolean;

  /** 채팅 패널 열림/닫힘 */
  isPanelOpen: boolean;
  openPanel: () => void;
  closePanel: () => void;
  togglePanel: () => void;

  /** 이력 뷰 (세션 목록 vs 대화) */
  isHistoryView: boolean;
  setHistoryView: (v: boolean) => void;
}

// ------------------------------------------------------------------ //
//  Constants
// ------------------------------------------------------------------ //

const ACTIVE_ROADMAP_KEY = "stepzero_active_roadmap_id";

// ------------------------------------------------------------------ //
//  Context
// ------------------------------------------------------------------ //

const ChatContext = createContext<ChatProviderValue | null>(null);

// ------------------------------------------------------------------ //
//  Provider
// ------------------------------------------------------------------ //

interface ChatProviderProps {
  children: ReactNode;
}

export function ChatProvider({ children }: ChatProviderProps) {
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [sessionListVersion, setSessionListVersion] = useState(0);
  const [sessionPreview, setSessionPreview] = useState<SessionPreview | null>(
    null,
  );
  const [sessionPreviewVersion, setSessionPreviewVersion] = useState(0);
  const [roadmapContext, setRoadmapContext] = useState<RoadmapContext | null>(
    null,
  );
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [isHistoryView, setHistoryView] = useState(false);

  const hasRoadmapContext =
    roadmapContext !== null && roadmapContext.stepId !== null;

  // ---- 로드맵 컨텍스트 로딩 ----

  const loadRoadmapContext = useCallback(async (roadmapId: string) => {
    try {
      const res = await apiClient.get<RoadmapDetailBrief>(
        `/roadmaps/${roadmapId}/detail`,
      );
      const steps = res.data.steps ?? [];
      const inProgress = steps.find((s) => s.status === "IN_PROGRESS");

      setRoadmapContext({
        roadmapId,
        stepId: inProgress?.id ?? null,
        stepTitle: inProgress?.title ?? null,
      });
    } catch {
      setRoadmapContext({ roadmapId, stepId: null, stepTitle: null });
    }
  }, []);

  const clearRoadmapContext = useCallback(() => {
    setRoadmapContext(null);
  }, []);

  // ---- 마운트 시 localStorage에서 active roadmap 로드 ----
  // .then() 콜백에서 setState → react-hooks/set-state-in-effect 회피

  useEffect(() => {
    const storedId = localStorage.getItem(ACTIVE_ROADMAP_KEY);
    if (!storedId) return;

    let cancelled = false;

    apiClient
      .get<RoadmapDetailBrief>(`/roadmaps/${storedId}/detail`)
      .then((res) => {
        if (cancelled) return;
        const steps = res.data.steps ?? [];
        const inProgress = steps.find((s) => s.status === "IN_PROGRESS");
        setRoadmapContext({
          roadmapId: storedId,
          stepId: inProgress?.id ?? null,
          stepTitle: inProgress?.title ?? null,
        });
      })
      .catch(() => {
        if (cancelled) return;
        setRoadmapContext({ roadmapId: storedId, stepId: null, stepTitle: null });
      });

    return () => {
      cancelled = true;
    };
  }, []);

  // ---- localStorage storage 이벤트 감지 (다른 탭 변경) ----

  useEffect(() => {
    const handleStorage = (e: StorageEvent) => {
      if (e.key !== ACTIVE_ROADMAP_KEY) return;

      const newId = e.newValue;
      if (!newId) {
        clearRoadmapContext();
        return;
      }

      loadRoadmapContext(newId);
    };

    window.addEventListener("storage", handleStorage);
    return () => window.removeEventListener("storage", handleStorage);
  }, [loadRoadmapContext, clearRoadmapContext]);

  // ---- 패널 제어 ----

  const openPanel = useCallback(() => setIsPanelOpen(true), []);
  const closePanel = useCallback(() => setIsPanelOpen(false), []);
  const togglePanel = useCallback(() => setIsPanelOpen((p) => !p), []);
  const refreshSessionList = useCallback(
    () => setSessionListVersion((prev) => prev + 1),
    [],
  );
  const publishSessionPreview = useCallback((session: SessionPreview) => {
    setSessionPreview(session);
    setSessionPreviewVersion((prev) => prev + 1);
  }, []);

  return (
    <ChatContext.Provider
      value={{
        currentSessionId,
        setCurrentSessionId,
        refreshSessionList,
        sessionListVersion,
        publishSessionPreview,
        sessionPreview,
        sessionPreviewVersion,
        roadmapContext,
        hasRoadmapContext,
        isPanelOpen,
        openPanel,
        closePanel,
        togglePanel,
        isHistoryView,
        setHistoryView,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
}

// ------------------------------------------------------------------ //
//  Hook
// ------------------------------------------------------------------ //

export function useChatProvider(): ChatProviderValue {
  const ctx = useContext(ChatContext);
  if (!ctx) {
    throw new Error("useChatProvider must be used within ChatProvider");
  }
  return ctx;
}
